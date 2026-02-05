from pathlib import Path


def read_bezeichnungen(file: Path) -> list[str]:
    # TODO: This will have to be a JSON where one says VE733: list of GWM
    # TODO: Add error msg if File does not exist
    with open(file, "r", encoding="utf-8") as f:
        return [b.replace("\n", "") for b in f.readlines()]
