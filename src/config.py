from dataclasses import dataclass


@dataclass
class AppConfig:
    package: str
    source: str
    test_mode: bool
    ascii_tree: bool
    max_depth: int
    filter_substring: str
    reverse: bool = False

    def as_key_value(self) -> str:
        lines = [
            f"package          = {self.package}",
            f"source           = {self.source}",
            f"test_mode        = {self.test_mode}",
            f"ascii_tree       = {self.ascii_tree}",
            f"max_depth        = {self.max_depth}",
            f"filter_substring = {self.filter_substring!r}",
            f"reverse          = {self.reverse}",
        ]
        return "\n".join(lines)