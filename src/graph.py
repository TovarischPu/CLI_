from typing import Callable, Dict, List, Set


class DependencyGraph:
    def __init__(self) -> None:
        self.adjacency_list: Dict[str, List[str]] = {}

    def add_edge(self, source: str, target: str) -> None:
        if source not in self.adjacency_list:
            self.adjacency_list[source] = []
        if target not in self.adjacency_list[source]:
            self.adjacency_list[source].append(target)
        if target not in self.adjacency_list:
            self.adjacency_list[target] = []

    def reverse(self) -> "DependencyGraph":
        rev = DependencyGraph()
        for source, targets in self.adjacency_list.items():
            if source not in rev.adjacency_list:
                rev.adjacency_list[source] = []
            for target in targets:
                if target not in rev.adjacency_list:
                    rev.adjacency_list[target] = []
                if source not in rev.adjacency_list[target]:
                    rev.adjacency_list[target].append(source)
        return rev

    def bfs(
        self,
        start: str,
        max_depth: int,
        filter_str: str,
    ) -> "DependencyGraph":
        result = DependencyGraph()
        if start not in self.adjacency_list:
            return result
        if filter_str and filter_str in start:
            return result

        visited: Set[str] = {start}

        def _process_level(current_level: List[str], depth: int) -> None:
            if not current_level or depth > max_depth:
                return
            next_level: List[str] = []
            for pkg in current_level:
                deps = self.adjacency_list.get(pkg, [])
                for dep in deps:
                    if dep in visited:
                        continue
                    if filter_str and filter_str in dep:
                        continue
                    result.add_edge(pkg, dep)
                    visited.add(dep)
                    next_level.append(dep)
            _process_level(next_level, depth + 1)

        _process_level([start], 1)
        return result
    def to_dot(self, root: str) -> str:
        lines: List[str] = ["digraph dependencies {"]
        lines.append("    rankdir=LR;")
        lines.append(
            '    node [shape=box, style=filled, '
            'fillcolor=lightblue, fontname=Arial];'
        )
        lines.append(
            f'    "{root}" [fillcolor=gold, '
            f'fontcolor=black, penwidth=2];'
        )
        for source, targets in self.adjacency_list.items():
            for target in targets:
                lines.append(f'    "{source}" -> "{target}";')
        lines.append("}")
        return "\n".join(lines)


class GraphBuilder:
    def __init__(
        self,
        max_depth: int,
        filter_str: str,
        fetch_func: Callable[[str], List[str]],
    ) -> None:
        self.max_depth = max_depth
        self.filter_str = filter_str
        self.fetch_func = fetch_func
        self.graph = DependencyGraph()
        self.visited: Set[str] = set()

    def _is_valid_package(self, pkg: str) -> bool:
        if self.filter_str and self.filter_str in pkg:
            return False
        return True

    def _process_level(self, current_level: List[str], depth: int) -> None:
        if not current_level or depth > self.max_depth:
            return
        next_level: List[str] = []
        for pkg in current_level:
            self.visited.add(pkg)
            deps = self.fetch_func(pkg)
            for dep in deps:
                if not self._is_valid_package(dep):
                    continue
                self.graph.add_edge(pkg, dep)
                if dep not in self.visited:
                    self.visited.add(dep)
                    next_level.append(dep)
        self._process_level(next_level, depth + 1)

    def build(self, start_pkg: str) -> DependencyGraph:
        if not self._is_valid_package(start_pkg):
            return self.graph
        self.visited.add(start_pkg)
        self._process_level([start_pkg], 1)
        return self.graph


def parse_test_file(file_path: str) -> Dict[str, List[str]]:
    dependencies: Dict[str, List[str]] = {}
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or ":" not in line:
                continue
            parts = line.split(":", 1)
            pkg = parts[0].strip()
            deps_str = parts[1].strip()
            if deps_str:
                deps = [d.strip() for d in deps_str.split(",")]
            else:
                deps = []
            dependencies[pkg] = deps
    return dependencies