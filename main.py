import datetime
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from src.persistence.sqlite import speichere_in_sqlite
from src.persistence.state import lade_data, speichere_data
from src.utils.logger import config_logger
from src.mainops.client import MainOpsClient, Zugangsdaten
from src.transform.measurements import data_verarbeiten

LOG_LEVEL = os.getenv("LOG_LEVEL").upper()

config_logger(__file__, LOG_LEVEL)

log = logging.getLogger(__name__)

SEIT = os.getenv("SEIT", "")
BIS = datetime.datetime.now().strftime("%d.%m.%Y")


def mainops_client_ausfuehren():
    zugangsdaten = Zugangsdaten(
        os.getenv("USERNAME", ""), 
        os.getenv("PASSWORD", ""),
    )
    client = MainOpsClient(zugangsdaten)

    # Auth an MainOps
    client.starte_session()
    client.anmelden()

    # Requests an MainOps
    projekte = [p for p in client.hole_projekte() if "Vergabeeinheit " in p.name]
    client.projekte = projekte

    client.hole_messungen(von=SEIT, bis=BIS)
    client.ermittle_messstellen()
    client.hole_offsets()

    speichere_data(client.state)

    return client

def into_db(state):
    if not state:
        state = lade_data()

    data = data_verarbeiten(state)

    speichere_in_sqlite(*data)


def main():
    client = mainops_client_ausfuehren()
    into_db(client.state)


if __name__ == "__main__":
    main()
