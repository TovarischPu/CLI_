import argparse
from typing import Sequence

from .config import AppConfig
from .validation import (
    ValidationError,
    validate_filter,
    validate_max_depth,
    validate_package,
    validate_source,
)

_DEFAULT_MAX_DEPTH = 5


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей Maven."
    )
    parser.add_argument(
        "--package", required=True,
        help="Имя анализируемого пакета",
    )
    parser.add_argument(
        "--source", required=True,
        help="URL репозитория или путь к тестовому файлу",
    )
    parser.add_argument(
        "--test-mode", action="store_true",
        help="Режим работы с тестовым репозиторием",
    )
    parser.add_argument(
        "--ascii-tree", action="store_true",
        help="Выводить зависимости в виде ASCII-дерева",
    )
    parser.add_argument(
        "--max-depth", type=int, default=_DEFAULT_MAX_DEPTH,
        help="Максимальная глубина анализа",
    )
    parser.add_argument(
        "--filter", default="",
        help="Подстрока для фильтрации пакетов",
    )
    parser.add_argument(
        "--reverse", action="store_true",
        help="Выводить обратные зависимости пакета",
    )
    return parser


def parse_args(argv: Sequence[str]) -> AppConfig:
    parser = _build_parser()
    args = parser.parse_args(argv)
    package = validate_package(args.package, args.test_mode)
    source = validate_source(args.source, args.test_mode)
    max_depth = validate_max_depth(args.max_depth)
    filter_substring = validate_filter(args.filter)
    return AppConfig(
        package=package,
        source=source,
        test_mode=args.test_mode,
        ascii_tree=args.ascii_tree,
        max_depth=max_depth,
        filter_substring=filter_substring,
        reverse=args.reverse,
    )


def safe_parse_args(argv: Sequence[str]) -> AppConfig:
    try:
        return parse_args(argv)
    except SystemExit as exc:
        raise ValidationError("Ошибка разбора аргументов") from exc