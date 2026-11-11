import streamlit as st

from data.campus import load_campus_data


st.set_page_config(page_title="VSSUT Building Information", layout="wide")
st.title("🏢 VSSUT Building Information")

campus = load_campus_data()
buildings = [node for node in campus["nodes"] if node["category"] != "Road junction" and node["id"] != "vssut-campus"]
by_name = {node["name"]: node for node in buildings}

building_name = st.selectbox("Select a campus building or facility", list(by_name))
building = by_name[building_name]
st.subheader(building["name"])
st.write(building["info"])
st.caption(f"Category: {building['category']}")

if building.get("latitude") is not None and building.get("longitude") is not None:
    st.success("Coordinates are stored for this location.")
    st.metric("Latitude", f"{building['latitude']:.7f}")
    st.metric("Longitude", f"{building['longitude']:.7f}")
    st.caption(f"Coordinate source: {building.get('coordinate_source', 'Not recorded')}")
else:
    st.info("Coordinates have not been verified yet. Search Google Places from the Campus Map or ask a campus administrator to add the point.")
