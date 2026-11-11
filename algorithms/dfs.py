from algorithms.graph import GRAPH


def dfs(start: str, goal: str, graph: dict[str, dict[str, float]] | None = None) -> list[str]:
    """Depth-first path search; the returned path is not guaranteed shortest."""
    graph = graph if graph is not None else GRAPH
    if start not in graph or goal not in graph:
        return []

    stack = [(start, [start])]
    visited = set()
    while stack:
        node, path = stack.pop()
        if node == goal:
            return path
        if node in visited:
            continue
        visited.add(node)
        for neighbor in reversed(list(graph[node])):
            if neighbor not in visited:
                stack.append((neighbor, path + [neighbor]))
    return []
