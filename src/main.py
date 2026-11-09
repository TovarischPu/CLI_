import os
import shutil
import subprocess
import sys
from typing import Sequence, List, Dict, Set

from .cli import safe_parse_args
from .downloader import download_text
from .graph import DependencyGraph, GraphBuilder, parse_test_file
from .parser import build_pom_url, parse_direct_dependencies
from .validation import ValidationError


def _fetch_real_deps(pkg: str, source: str) -> List[str]:
    url = build_pom_url(source, pkg)
    print(f"[INFO] Загрузка: {url}")
    try:
        xml_content = download_text(url)
        deps = parse_direct_dependencies(xml_content)
        return [
            f"{d['groupId']}:{d['artifactId']}:{d['version']}"
            for d in deps
        ]
    except RuntimeError as exc:
        print(f"[WARN] {exc}")
        return []


def _fetch_test_deps(pkg: str, data: Dict[str, List[str]]) -> List[str]:
    return data.get(pkg, [])


def _print_graph(graph: DependencyGraph) -> None:
    print("\nПостроенный граф зависимостей:")
    for source, targets in graph.adjacency_list.items():
        if targets:
            targets_str = ", ".join(targets)
            print(f"  {source} -> {targets_str}")
        else:
            print(f"  {source} -> (нет зависимостей)")


def _print_reverse_graph(
    graph: DependencyGraph, target: str
) -> None:
    print(f"\nОбратные зависимости для пакета [{target}]:")
    has_any = False
    for source, targets in graph.adjacency_list.items():
        if targets:
            has_any = True
            targets_str = ", ".join(targets)
            print(f"  {source} -> {targets_str}")
    if not has_any:
        print("  (нет обратных зависимостей)")


def _print_ascii_tree(
    graph: DependencyGraph, root: str, title: str
) -> None:
    print(f"\n{title} [{root}]:")
    print(root)
    if root not in graph.adjacency_list:
        return

    def _walk(
        pkg: str, prefix: str, is_last: bool, path: Set[str]
    ) -> None:
        connector = "└── " if is_last else "├── "
        if pkg in path:
            print(f"{prefix}{connector}{pkg} (cycle)")
            return
        print(f"{prefix}{connector}{pkg}")
        children = graph.adjacency_list.get(pkg, [])
        new_path = path | {pkg}
        for i, child in enumerate(children):
            last_child = (i == len(children) - 1)
            extension = "    " if is_last else "│   "
            _walk(child, prefix + extension, last_child, new_path)

    children = graph.adjacency_list.get(root, [])
    for i, child in enumerate(children):
        last_child = (i == len(children) - 1)
        _walk(child, "", last_child, {root})


def _render_graphviz(
    graph: DependencyGraph, root: str, title: str
) -> None:
    if not shutil.which("dot"):
        return

    dot_content = graph.to_dot(root)
    print(f"\n{title} (DOT):")
    print(dot_content)

    dot_filename = "graph_deps.dot"
    png_filename = "graph_deps.png"
    
    try:
        with open(dot_filename, "w", encoding="utf-8") as f:
            f.write(dot_content)
            
        subprocess.run(
            ["dot", "-Tpng", dot_filename, "-o", png_filename],
            check=True,
            capture_output=True,
        )
        
        abs_png_path = os.path.abspath(png_filename)
        print(f"\n[INFO] PNG сохранён: {abs_png_path}")
        print("[INFO] Откройте файл в графическом просмотрщике")
        
    except subprocess.CalledProcessError as exc:
        print(
            f"[ERROR] Ошибка Graphviz: {exc.stderr.decode()}",
            file=sys.stderr,
        )


def run(argv: Sequence[str]) -> int:
    try:
        config = safe_parse_args(argv)
    except ValidationError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    print("=== Конфигурация приложения ===")
    print(config.as_key_value())
    print("=== Конец конфигурации ===")
    if config.test_mode:
        print(f"\n[INFO] Тестовый режим. Файл: {config.source}")
        try:
            test_data = parse_test_file(config.source)
            fetch_func = lambda pkg: _fetch_test_deps(pkg, test_data)
        except FileNotFoundError:
            print(
                f"[ERROR] Файл не найден: {config.source}",file=sys.stderr,)
            return 1
    else:
        fetch_func = lambda pkg: _fetch_real_deps(pkg, config.source)

    builder = GraphBuilder(
        max_depth=config.max_depth,
        filter_str=config.filter_substring,
        fetch_func=fetch_func,
    )
    graph = builder.build(config.package)

    if config.reverse:
        rev_graph = graph.reverse()
        result = rev_graph.bfs(config.package,config.max_depth,
                               config.filter_substring,)
        if config.ascii_tree:_print_ascii_tree(result,config.package,"Обр аски")
        else:
            _render_graphviz(result, config.package,"Обр зависимости",)
    else:
        if config.ascii_tree:_print_ascii_tree(graph,config.package,"Прям аски")
        else:_render_graphviz(graph, config.package,"Прямые",)
    return 0
def main() -> None:
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()