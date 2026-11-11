import heapq
import math

from algorithms.graph import GRAPH


def _haversine_m(left: dict, right: dict) -> float:
    earth_radius_m = 6_371_000
    lat1, lon1 = math.radians(left["latitude"]), math.radians(left["longitude"])
    lat2, lon2 = math.radians(right["latitude"]), math.radians(right["longitude"])
    d_lat, d_lon = lat2 - lat1, lon2 - lon1
    value = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    return 2 * earth_radius_m * math.asin(min(1, math.sqrt(value)))


def astar(
    start: str,
    goal: str,
    graph: dict[str, dict[str, float]] | None = None,
    nodes: dict[str, dict] | None = None,
    use_coordinates: bool = False,
) -> tuple[list[str], float]:
    """Return a minimum-distance path using an admissible heuristic.

    The geometric lower bound is enabled only when the caller confirms every
    edge/coordinate in this graph is verified. A zero heuristic remains
    admissible for demonstration or partially verified campus data.
    """
    graph = graph if graph is not None else GRAPH
    if start not in graph or goal not in graph:
        return [], 0.0

    def heuristic(node_id: str) -> float:
        if not use_coordinates or not nodes:
            return 0.0
        here, target = nodes.get(node_id, {}), nodes.get(goal, {})
        if None in (here.get("latitude"), here.get("longitude"), target.get("latitude"), target.get("longitude")):
            return 0.0
        return _haversine_m(here, target)

    frontier = [(heuristic(start), 0.0, start)]
    best_distance = {start: 0.0}
    parent: dict[str, str | None] = {start: None}

    while frontier:
        _, distance, node = heapq.heappop(frontier)
        if distance != best_distance.get(node):
            continue
        if node == goal:
            path = []
            current: str | None = goal
            while current is not None:
                path.append(current)
                current = parent[current]
            return list(reversed(path)), distance

        for neighbor, edge_distance in graph[node].items():
            candidate = distance + edge_distance
            if candidate < best_distance.get(neighbor, float("inf")):
                best_distance[neighbor] = candidate
                parent[neighbor] = node
                heapq.heappush(frontier, (candidate + heuristic(neighbor), candidate, neighbor))

    return [], 0.0
