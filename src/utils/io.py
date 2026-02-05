from pathlib import Path


def read_bezeichnungen(file: Path) -> list[str]:
    # TODO: Add error msg if File does not exist
    with open(file, "r", encoding="utf-8") as f:
        return [b.replace("\n", "") for b in f.readlines()]
