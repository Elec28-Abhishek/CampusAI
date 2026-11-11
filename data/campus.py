"""Campus location and road graph storage for VSSUT."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DATA_PATH = Path(__file__).with_name("campus_graph.json")


def load_campus_data() -> dict[str, Any]:
    with DATA_PATH.open("r", encoding="utf-8") as source:
        return json.load(source)


def save_campus_data(data: dict[str, Any]) -> None:
    temporary_path = DATA_PATH.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as output:
        json.dump(data, output, indent=2, ensure_ascii=False)
        output.write("\n")
    temporary_path.replace(DATA_PATH)


def node_index(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {node["id"]: node for node in data.get("nodes", [])}


def graph_from_data(data: dict[str, Any]) -> dict[str, dict[str, float]]:
    graph = {node["id"]: {} for node in data.get("nodes", [])}
    for edge in data.get("edges", []):
        start, end = edge.get("from"), edge.get("to")
        distance = edge.get("distance_m")
        if start in graph and end in graph and isinstance(distance, (int, float)) and distance > 0:
            graph[start][end] = float(distance)
            graph[end][start] = float(distance)
    return graph


def path_uses_only_verified_edges(data: dict[str, Any], path: list[str]) -> bool:
    if len(path) < 2:
        return False
    edge_index = {
        frozenset((edge.get("from"), edge.get("to"))): edge
        for edge in data.get("edges", [])
    }
    return all(
        (edge := edge_index.get(frozenset((left, right)))) is not None
        and edge.get("verified") is True
        for left, right in zip(path, path[1:])
    )


def path_has_coordinates(data: dict[str, Any], path: list[str]) -> bool:
    nodes = node_index(data)
    return bool(path) and all(
        nodes.get(node_id, {}).get("latitude") is not None
        and nodes.get(node_id, {}).get("longitude") is not None
        for node_id in path
    )


def path_distance(data: dict[str, Any], path: list[str]) -> float:
    graph = graph_from_data(data)
    return sum(graph[left][right] for left, right in zip(path, path[1:]))
