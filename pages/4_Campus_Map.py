from __future__ import annotations

import hmac
import math
from datetime import datetime, timezone
from urllib.parse import urlencode

import streamlit as st
from PIL import Image

from algorithms.astar import astar
from algorithms.bfs import bfs
from algorithms.dfs import dfs
from data.campus import (
    graph_from_data,
    load_campus_data,
    node_index,
    path_distance,
    path_has_coordinates,
    path_uses_only_verified_edges,
    save_campus_data,
)
from utils.google_map_component import google_map
from utils.maps_config import campus_admin_password, google_maps_browser_key


st.set_page_config(page_title="VSSUT Campus Navigation", page_icon="🗺️", layout="wide")
st.title("🗺️ CampusAI · VSSUT Navigation")
st.caption("Veer Surendra Sai University of Technology · Burla, Sambalpur, Odisha, India")
st.write("Choose a VSSUT starting location and destination, then open walking directions in Google Maps. Add a Google Maps key to search campus places and view the interactive map inside CampusAI.")

campus_data = load_campus_data()
all_nodes = campus_data.get("nodes", [])
nodes_by_id = node_index(campus_data)
graph = graph_from_data(campus_data)
route_nodes = [node for node in all_nodes if node["id"] != "vssut-campus" and node["category"] != "Road junction"]
name_by_id = {node["id"]: node["name"] for node in all_nodes}


def _normalize_name(value: str) -> str:
    value = value.lower()
    for phrase in ("veer surendra sai university of technology", "vssut", "department of", "department", "burla", "odisha", "india"):
        value = value.replace(phrase, " ")
    return " ".join("".join(char if char.isalnum() else " " for char in value).split())


def _graph_node_for_place(name: str) -> str | None:
    candidate = _normalize_name(name)
    matches = []
    for node in route_nodes:
        known = _normalize_name(node["name"])
        if candidate == known or (known and known in candidate) or (candidate and candidate in known):
            matches.append((len(known), node["id"]))
    return max(matches)[1] if matches else None


def _route_choice_records() -> dict[str, dict]:
    choices = {}
    for node in route_nodes:
        choices[f"node:{node['id']}"] = {
            "label": f"{node['name']} · {'verified pin' if node.get('latitude') is not None else 'pin not verified'}", "id": node["id"], "node_id": node["id"],
            "latitude": node.get("latitude"), "longitude": node.get("longitude"),
            "place_id": node.get("google_place_id"), "source": node.get("coordinate_source"),
            "coordinates_verified": node.get("coordinates_verified", False),
            "maps_query": node.get("maps_query"),
        }
    for place in st.session_state.get("vssut_google_places", []):
        place_id = place.get("id")
        if not place_id:
            continue
        choices[f"place:{place_id}"] = {
            "label": f"{place.get('name', 'Google place')} · Google Places",
            "id": place_id,
            "node_id": _graph_node_for_place(place.get("name", "")),
            "latitude": place.get("latitude"), "longitude": place.get("longitude"),
            "place_id": place_id, "source": "Google Places",
        }
    clicked = st.session_state.get("vssut_map_click")
    if clicked:
        lat, lng = clicked.get("latitude"), clicked.get("longitude")
        if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
            key = f"map:{lat:.7f},{lng:.7f}"
            choices[key] = {
                "label": f"Selected map point · {lat:.5f}, {lng:.5f}",
                "id": key, "node_id": None, "latitude": lat, "longitude": lng,
                "place_id": None, "source": "Selected map point",
            }
    return choices


choices = _route_choice_records()
choice_ids = list(choices)
default_start = "node:main-gate" if "node:main-gate" in choices else choice_ids[0]
default_end = "node:central-library" if "node:central-library" in choices else choice_ids[min(1, len(choice_ids) - 1)]
left, right = st.columns(2)
with left:
    start_key = st.selectbox(
        "📍 Starting location",
        choice_ids,
        index=choice_ids.index(default_start),
        format_func=lambda choice: choices[choice]["label"],
        key="vssut_start_choice",
    )
with right:
    end_key = st.selectbox(
        "🎯 Destination",
        choice_ids,
        index=choice_ids.index(default_end),
        format_func=lambda choice: choices[choice]["label"],
        key="vssut_end_choice",
    )
start = choices[start_key]
end = choices[end_key]


def _map_point(choice: dict) -> dict | None:
    if choice.get("latitude") is None or choice.get("longitude") is None:
        return None
    return {
        "id": choice["id"],
        "place_id": choice.get("place_id"),
        "label": choice["label"],
        "latitude": choice["latitude"],
        "longitude": choice["longitude"],
    }


def _google_maps_directions_url(origin: dict, destination: dict) -> str:
    def query_for(choice: dict) -> tuple[str, str | None]:
        node_id = choice.get("node_id")
        if choice.get("maps_query"):
            name = choice["maps_query"]
        elif node_id:
            name = name_by_id.get(node_id, choice["label"])
        else:
            name = choice["label"].replace(" · Google Places", "")
        contextual_name = (
            name if "vssut" in name.lower() or "burla" in name.lower()
            else f"{name}, Veer Surendra Sai University of Technology, Burla, Odisha, India"
        )

        if choice.get("source") == "Selected map point":
            return f"{choice['latitude']},{choice['longitude']}", None
        if choice.get("place_id"):
            return contextual_name, choice["place_id"]
        if choice.get("coordinates_verified") and choice.get("latitude") is not None:
            return f"{choice['latitude']},{choice['longitude']}", None
        return contextual_name, None

    origin_query, origin_place_id = query_for(origin)
    destination_query, destination_place_id = query_for(destination)
    parameters = {
        "api": "1",
        "origin": origin_query,
        "destination": destination_query,
        "travelmode": "walking",
    }
    if origin_place_id:
        parameters["origin_place_id"] = origin_place_id
    if destination_place_id:
        parameters["destination_place_id"] = destination_place_id
    return "https://www.google.com/maps/dir/?" + urlencode(parameters)


if start_key == end_key:
    st.info("Choose two different places to get walking directions.")
else:
    directions_url = _google_maps_directions_url(start, end)
    st.link_button("🧭 Open walking directions in Google Maps", directions_url, type="primary")
    if not start.get("coordinates_verified") or not end.get("coordinates_verified"):
        if start.get("place_id") and end.get("place_id"):
            pass
        else:
            st.caption("Some selected campus pins are unverified. Check the start and destination Google Maps chooses before walking.")


algorithm_results = []
algorithm_routes_for_map = []
start_node, end_node = start.get("node_id"), end.get("node_id")
if start_node and end_node and start_node in graph and end_node in graph and start_node != end_node:
    all_edges_verified = all(edge.get("verified") is True for edge in campus_data.get("edges", []))
    all_graph_coordinates = all(
        nodes_by_id.get(node_id, {}).get("latitude") is not None
        and nodes_by_id.get(node_id, {}).get("longitude") is not None
        for node_id in graph
    )
    coordinate_heuristic_is_safe = all_edges_verified and all_graph_coordinates
    routes = [
        ("BFS", bfs(start_node, end_node, graph)),
        ("DFS", dfs(start_node, end_node, graph)),
    ]
    astar_path, _ = astar(
        start_node, end_node, graph, nodes_by_id,
        use_coordinates=coordinate_heuristic_is_safe,
    )
    routes.append(("A*", astar_path))

    for algorithm_name, path in routes:
        if not path:
            algorithm_results.append({
                "Algorithm": algorithm_name,
                "Path": "No connected path in the current campus graph",
                "Distance (m)": None,
                "Walk time (min)": None,
                "Data status": "No path",
            })
            continue
        distance = path_distance(campus_data, path)
        verified = path_uses_only_verified_edges(campus_data, path)
        status = "Verified graph data" if verified else "Sample/partially verified graph data"
        algorithm_results.append({
            "Algorithm": algorithm_name,
            "Path": " → ".join(name_by_id.get(node_id, node_id) for node_id in path),
            "Distance (m)": round(distance),
            "Walk time (min)": round(distance / 75, 1),
            "Data status": status,
        })
        path_points = [nodes_by_id.get(node_id, {}) for node_id in path]
        algorithm_routes_for_map.append({
            "name": algorithm_name,
            "coordinates": [
                {"latitude": point["latitude"], "longitude": point["longitude"]}
                for point in path_points
                if point.get("latitude") is not None and point.get("longitude") is not None
            ] if path_has_coordinates(campus_data, path) and path_uses_only_verified_edges(campus_data, path) else [],
        })

st.divider()
api_key = google_maps_browser_key()
map_event = None
if api_key:
    map_event = google_map(
        api_key=api_key,
        viewport=campus_data["university"]["initial_viewport"],
        buildings=[node for node in all_nodes if node.get("latitude") is not None and node.get("longitude") is not None],
        boundary=campus_data["university"].get("boundary"),
        discovered_places=st.session_state.get("vssut_google_places", []),
        origin=_map_point(start),
        destination=_map_point(end),
        algorithm_routes=algorithm_routes_for_map,
        map_click=st.session_state.get("vssut_map_click"),
        key="vssut_google_map",
    )
    if isinstance(map_event, dict):
        event_id = map_event.get("event_id")
        if event_id and event_id != st.session_state.get("vssut_last_map_event"):
            st.session_state["vssut_last_map_event"] = event_id
            if map_event.get("type") == "search_results":
                known_places = {
                    place.get("id"): place
                    for place in st.session_state.get("vssut_google_places", [])
                    if place.get("id")
                }
                known_places.update({
                    place.get("id"): place
                    for place in map_event.get("places", [])
                    if place.get("id")
                })
                st.session_state["vssut_google_places"] = list(known_places.values())
                st.session_state.pop("vssut_google_place_error", None)
            elif map_event.get("type") == "places_error":
                st.session_state["vssut_google_place_error"] = map_event.get("message", "Google Places search failed.")
            elif map_event.get("type") == "map_click":
                st.session_state["vssut_map_click"] = {
                    "latitude": map_event.get("lat"),
                    "longitude": map_event.get("lng"),
                    "event_id": event_id,
                }
            elif map_event.get("type") == "place_selected":
                place = map_event.get("place")
                if place and place.get("id"):
                    known = {item.get("id") for item in st.session_state.get("vssut_google_places", [])}
                    if place["id"] not in known:
                        st.session_state["vssut_google_places"] = st.session_state.get("vssut_google_places", []) + [place]
            elif map_event.get("type") in {"google_route", "google_route_error"}:
                st.session_state["vssut_google_route"] = map_event.get("route")
            elif map_event.get("type") == "maps_error":
                st.session_state["vssut_maps_api_error"] = map_event.get("message", "Google Maps could not be loaded.")
            st.rerun()
else:
    st.warning(
        "No Google Maps key was found. The walking-directions button above still works without one. To show the interactive map and use in-app Places search/directions, set GOOGLE_MAPS_BROWSER_API_KEY and enable billing plus Maps JavaScript API, Places API, and Routes API."
    )

maps_api_error = st.session_state.get("vssut_maps_api_error")
if maps_api_error:
    st.error(f"Google Maps is unavailable: {maps_api_error}")
places_error = st.session_state.get("vssut_google_place_error")
if places_error:
    st.warning(f"Google Places search is unavailable: {places_error}")

if not api_key or maps_api_error:
    with st.expander("Optional: upload a static VSSUT map image"):
        uploaded_map = st.file_uploader(
            "Upload a VSSUT campus map image (PNG or JPG)",
            type=["png", "jpg", "jpeg"],
            key="vssut_fallback_map_upload",
        )
        if uploaded_map is not None:
            try:
                st.image(Image.open(uploaded_map), caption="Uploaded VSSUT map image · static reference, not Google Maps", use_container_width=True)
            except Exception:
                st.error("This image could not be opened. Upload a valid PNG or JPG map.")

current_origin = _map_point(start)
current_destination = _map_point(end)
google_route = st.session_state.get("vssut_google_route") or {}
if not api_key or maps_api_error:
    st.info("The button above opens walking directions in Google Maps. An API key is needed only for the interactive map and in-app Places search/directions.")
elif current_origin and current_destination:
    expected_signature = "|".join([
        current_origin.get("place_id") or current_origin.get("id") or f"{current_origin['latitude']},{current_origin['longitude']}",
        current_destination.get("place_id") or current_destination.get("id") or f"{current_destination['latitude']},{current_destination['longitude']}",
    ])
    if google_route.get("signature") == expected_signature and google_route.get("type") == "google_route":
        st.markdown("#### Google Maps walking directions")
        g1, g2 = st.columns(2)
        g1.metric("Google route distance", f"{google_route.get('distance_m', 0):,.0f} m")
        g2.metric("Google estimated walking time", f"{max(1, round(google_route.get('duration_ms', 0) / 60000))} min")
        steps = google_route.get("steps") or []
        if steps:
            with st.expander("Walking instructions"):
                for step_number, step in enumerate(steps, start=1):
                    st.write(f"{step_number}. {step}")
    elif google_route.get("signature") == expected_signature and google_route.get("type") == "google_route_error":
        st.warning(google_route.get("message", "Google Maps could not calculate this route."))
    else:
        st.info("Google walking directions will appear on the map when Routes API returns a route for both selected locations.")
else:
    missing = []
    if not current_origin:
        missing.append("starting location")
    if not current_destination:
        missing.append("destination")
    st.info(
        "Google walking directions need coordinates or a Google Place ID for the "
        + " and ".join(missing)
        + ". Search and select a Google Places match above, select a point on the map, or ask an administrator to verify a pin."
    )

with st.expander("Optional: compare BFS, DFS, and A* graph routes"):
    if start_node and end_node and start_node == end_node:
        st.info("Choose two different graph locations to compare routes.")
    elif start_node and end_node and algorithm_results:
        st.dataframe(algorithm_results, hide_index=True, use_container_width=True)
        if any(row["Data status"] != "Verified graph data" for row in algorithm_results if row["Path"] != "No connected path in the current campus graph"):
            st.warning("This campus graph still contains demonstration or unverified edges. Sample distances and paths are illustrative and do not represent confirmed pedestrian routes.")
        st.caption("BFS minimizes edge count; DFS does not guarantee a shortest route; A* minimizes edge distance. A* uses a zero admissible heuristic until all graph edges and node coordinates are verified. Algorithm walk times are rough estimates at 75 m/min. Google walking directions are a separate Google Routes API result.")
    elif start_node is None or end_node is None:
        st.info("This Google Places result or map point is not connected to the campus graph. Google directions may still work; graph comparison needs an administrator to add the location and verified paths.")
    else:
        st.info("No campus graph route is available for this pair.")

with st.expander("Campus data readiness"):
    unlocated = [node["name"] for node in route_nodes if node.get("latitude") is None or node.get("longitude") is None]
    if campus_data["university"].get("boundary"):
        st.success("A verified VSSUT campus boundary is configured and shown on the map.")
    else:
        st.info("No verified VSSUT campus boundary polygon is configured yet, so none is drawn.")
    st.caption(f"{len(unlocated)} listed buildings/facilities still need verified coordinates. A Google Places search may find a result; unlisted internal locations need an administrator-confirmed pin.")

with st.expander("Administrator · verify campus locations and paths"):
    configured_password = campus_admin_password()
    if not configured_password:
        st.warning("Set CAMPUS_ADMIN_PASSWORD in environment variables or Streamlit secrets to unlock campus data editing.")
    else:
        if not st.session_state.get("vssut_admin_authenticated"):
            password = st.text_input("Campus administrator password", type="password", key="vssut_admin_password_input")
            if st.button("Unlock campus editor", key="vssut_admin_unlock"):
                if hmac.compare_digest(password, configured_password):
                    st.session_state["vssut_admin_authenticated"] = True
                    st.rerun()
                st.error("That password did not match.")
        else:
            if st.button("Lock campus editor", key="vssut_admin_lock"):
                st.session_state["vssut_admin_authenticated"] = False
                st.session_state.pop("vssut_admin_password_input", None)
                st.rerun()
            st.caption("When Google Maps is available, click the point and confirm it is the correct VSSUT building before saving. If the map is unavailable, enter a coordinate only when you have independently verified it. The graph currently contains clearly labelled sample edges.")
            editor_node_ids = [node["id"] for node in all_nodes if node["id"] != "vssut-campus"]
            editor_node_id = st.selectbox(
                "Location to edit",
                editor_node_ids,
                format_func=lambda node_id: f"{name_by_id[node_id]} · {nodes_by_id[node_id]['category']}",
                key="vssut_admin_node",
            )
            pending_click = st.session_state.get("vssut_map_click")
            pending_click_id = pending_click.get("event_id") if pending_click else None
            applied_click_id = st.session_state.get("vssut_admin_applied_click")
            if pending_click and pending_click_id != applied_click_id:
                st.session_state[f"vssut_admin_lat_{editor_node_id}"] = float(pending_click["latitude"])
                st.session_state[f"vssut_admin_lng_{editor_node_id}"] = float(pending_click["longitude"])
                st.session_state["vssut_admin_applied_click"] = pending_click_id
            selected_node = nodes_by_id[editor_node_id]
            available_google_places = st.session_state.get("vssut_google_places", [])
            if available_google_places:
                st.markdown("##### Confirm a Google Places match")
                google_place_ids = [place["id"] for place in available_google_places if place.get("id")]
                google_place_by_id = {place["id"]: place for place in available_google_places if place.get("id")}
                if google_place_ids:
                    selected_google_place_id = st.selectbox(
                        "Google Places result for this building",
                        google_place_ids,
                        format_func=lambda place_id: f"{google_place_by_id[place_id].get('name', 'Google place')} · {google_place_by_id[place_id].get('address', '')}",
                        key="vssut_admin_google_place",
                    )
                    google_verified_by = st.text_input("Verified by", key=f"vssut_admin_google_verified_by_{editor_node_id}", placeholder="Administrator name or initials")
                    google_place_confirmed = st.checkbox(
                        f"I confirmed that this Google Places result is {selected_node['name']}",
                        key=f"vssut_admin_google_place_confirmed_{editor_node_id}",
                    )
                    if st.button("Save confirmed Google Places coordinates", key="vssut_save_google_place"):
                        selected_place = google_place_by_id[selected_google_place_id]
                        if not google_place_confirmed or not google_verified_by.strip():
                            st.error("Confirm the match and identify who verified it.")
                        else:
                            campus_anchor = campus_data["university"]["initial_viewport"]
                            approx_distance = math.hypot(
                                (float(selected_place["latitude"]) - campus_anchor["latitude"]) * 111_000,
                                (float(selected_place["longitude"]) - campus_anchor["longitude"]) * 103_000,
                            )
                            if approx_distance > 10_000:
                                st.error("This Google Places result is over 10 km from the VSSUT campus viewport. Search for a closer VSSUT result.")
                            else:
                                selected_node.update({
                                    "latitude": float(selected_place["latitude"]),
                                    "longitude": float(selected_place["longitude"]),
                                    "google_place_id": selected_place["id"],
                                    "coordinate_source": "Google Places (New) result, confirmed by administrator",
                                    "coordinate_source_url": selected_place.get("google_maps_url", ""),
                                    "coordinate_verified_by": google_verified_by.strip(),
                                    "coordinate_verified_at": datetime.now(timezone.utc).isoformat(),
                                    "coordinates_verified": True,
                                })
                                save_campus_data(campus_data)
                                st.success(f"Saved the confirmed Google Places location for {selected_node['name']}.")
                                st.rerun()
            default_latitude = selected_node.get("latitude")
            default_longitude = selected_node.get("longitude")
            lat_key, lng_key = f"vssut_admin_lat_{editor_node_id}", f"vssut_admin_lng_{editor_node_id}"
            if lat_key not in st.session_state:
                st.session_state[lat_key] = float(default_latitude) if default_latitude is not None else 21.49621099
            if lng_key not in st.session_state:
                st.session_state[lng_key] = float(default_longitude) if default_longitude is not None else 83.90458073
            with st.form("vssut_save_coordinate"):
                lat_col, lng_col = st.columns(2)
                latitude = lat_col.number_input("Latitude", min_value=-90.0, max_value=90.0, format="%.7f", key=lat_key)
                longitude = lng_col.number_input("Longitude", min_value=-180.0, max_value=180.0, format="%.7f", key=lng_key)
                verified_by = st.text_input("Verified by", placeholder="Administrator name or initials")
                source_note = st.text_input("Verification note", placeholder="For example: checked against campus signage / official plan")
                confirm_location = st.checkbox("I verified that this point is the selected VSSUT location")
                save_location = st.form_submit_button("Save verified coordinates")
            if save_location:
                campus_anchor = campus_data["university"]["initial_viewport"]
                # Reject accidental points far outside Burla while leaving room for the full campus.
                approx_distance = math.hypot(
                    (latitude - campus_anchor["latitude"]) * 111_000,
                    (longitude - campus_anchor["longitude"]) * 103_000,
                )
                if not confirm_location or not verified_by.strip() or not source_note.strip():
                    st.error("Confirm the location and provide who verified it plus a short source note.")
                elif approx_distance > 10_000:
                    st.error("This point is over 10 km from the VSSUT campus viewport. Select a point in the VSSUT campus area.")
                else:
                    target = nodes_by_id[editor_node_id]
                    target.update({
                        "latitude": float(latitude),
                        "longitude": float(longitude),
                        "coordinate_source": f"Administrator verification: {source_note.strip()}",
                        "coordinate_verified_by": verified_by.strip(),
                        "coordinate_verified_at": datetime.now(timezone.utc).isoformat(),
                        "coordinates_verified": True,
                    })
                    if "google_place_id" in target:
                        target.pop("google_place_id")
                    save_campus_data(campus_data)
                    st.success(f"Saved verified coordinates for {target['name']}.")
                    st.rerun()

            st.markdown("##### Add a verified pedestrian graph connection")
            edge_left, edge_right = st.columns(2)
            edge_start = edge_left.selectbox("From", editor_node_ids, format_func=lambda node_id: name_by_id[node_id], key="vssut_edge_from")
            edge_end = edge_right.selectbox("To", editor_node_ids, format_func=lambda node_id: name_by_id[node_id], key="vssut_edge_to")
            with st.form("vssut_save_edge"):
                edge_distance = st.number_input("Verified path distance (meters)", min_value=1, max_value=10000, value=100, step=1)
                edge_source = st.text_input("How was this path and distance verified?", placeholder="Campus plan, measured walk, or survey reference")
                edge_verified_by = st.text_input("Verified by", placeholder="Administrator name or initials")
                verified_path = st.checkbox("I verified this pedestrian connection and its distance")
                save_edge = st.form_submit_button("Save graph connection")
            if save_edge:
                if edge_start == edge_end:
                    st.error("Choose two different locations for a graph connection.")
                elif not verified_path or not edge_source.strip() or not edge_verified_by.strip():
                    st.error("Confirm verification and provide who verified the path plus a source note.")
                else:
                    pair = {edge_start, edge_end}
                    campus_data["edges"] = [
                        edge for edge in campus_data.get("edges", [])
                        if {edge.get("from"), edge.get("to")} != pair
                    ]
                    campus_data["edges"].append({
                        "from": edge_start,
                        "to": edge_end,
                        "distance_m": int(edge_distance),
                        "source": edge_source.strip(),
                        "verified": True,
                        "verified_by": edge_verified_by.strip(),
                        "verified_at": datetime.now(timezone.utc).isoformat(),
                    })
                    campus_data["graph_data_status"] = "verified" if all(edge.get("verified") is True for edge in campus_data["edges"]) else "mixed"
                    save_campus_data(campus_data)
                    st.success(f"Saved the verified connection: {name_by_id[edge_start]} → {name_by_id[edge_end]} ({edge_distance} m).")
                    st.rerun()

            sample_edge_indexes = [
                index for index, edge in enumerate(campus_data.get("edges", []))
                if edge.get("verified") is not True
            ]
            if sample_edge_indexes:
                st.markdown("##### Remove a demonstration connection")
                with st.form("vssut_remove_sample_edge"):
                    sample_edge_index = st.selectbox(
                        "Sample connection",
                        sample_edge_indexes,
                        format_func=lambda index: (
                            f"{name_by_id[campus_data['edges'][index]['from']]} ↔ "
                            f"{name_by_id[campus_data['edges'][index]['to']]} · "
                            f"{campus_data['edges'][index]['distance_m']} m (sample)"
                        ),
                    )
                    confirm_remove_sample = st.checkbox("I understand that removing this sample connection may disconnect demonstration paths")
                    remove_sample_edge = st.form_submit_button("Remove sample connection")
                if remove_sample_edge:
                    if not confirm_remove_sample:
                        st.error("Confirm removal before changing the demonstration graph.")
                    else:
                        removed_edge = campus_data["edges"].pop(sample_edge_index)
                        campus_data["graph_data_status"] = "verified" if all(edge.get("verified") is True for edge in campus_data["edges"]) else "mixed"
                        save_campus_data(campus_data)
                        st.success(f"Removed the sample connection between {name_by_id[removed_edge['from']]} and {name_by_id[removed_edge['to']]}.")
                        st.rerun()
