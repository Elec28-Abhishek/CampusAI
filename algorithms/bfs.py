from collections import deque

from algorithms.graph import GRAPH


def bfs(start: str, goal: str, graph: dict[str, dict[str, float]] | None = None) -> list[str]:
    """Find a path with the fewest edges in an unweighted view of the graph."""
    graph = graph if graph is not None else GRAPH
    if start not in graph or goal not in graph:
        return []

    queue = deque([start])
    parent: dict[str, str | None] = {start: None}
    while queue:
        node = queue.popleft()
        if node == goal:
            break
        for neighbor in graph[node]:
            if neighbor not in parent:
                parent[neighbor] = node
                queue.append(neighbor)

    if goal not in parent:
        return []
    path = []
    current: str | None = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    return list(reversed(path))
