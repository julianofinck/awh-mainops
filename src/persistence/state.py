import logging
import pickle
from pathlib import Path

from src.mainops.models import MainOpsState

log = logging.getLogger(__name__)


STATE = "data/mainops_state.pkl"


def speichere_data(
    state: MainOpsState,
    datei: str = STATE,
) -> None:

    with open(datei, "wb") as f:
        pickle.dump(state, f)


def lade_data(
    datei: str = STATE,
) -> MainOpsState:

    with open(datei, "rb") as f:
        return pickle.load(f)
