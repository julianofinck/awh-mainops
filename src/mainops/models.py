from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Projekt:
    id: int
    name: str


@dataclass
class Zugangsdaten:
    email: str
    passwort: str


@dataclass
class MainOpsState:
    projekte: list[Projekt]
    messungen: pd.DataFrame
    messstellen: list[str]
    bezugshoehen: pd.DataFrame
