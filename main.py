import os
from pathlib import Path

from dotenv import load_dotenv

from src.data.database import save_measurements
from src.scraper import get_messungen
from src.utils.io import read_bezeichnungen
from use_case.mainops_client import (Zugangsdaten, MainOpsClient, hole_eindeutig_und_sortiert_speichern)

load_dotenv()

def main():
    zugangsdaten = Zugangsdaten(
        os.getenv("USERNAME", ""), 
        os.getenv("PASSWORD", "")
    )
    client = MainOpsClient(zugangsdaten)
    client.starte_session()
    client.anmelden()


    """
    Welches Projekt?
    86 '2. S-Bahn-Stammstrecke München'
    85 'OB-West'
    88 'Rettungsschacht 4'
    80 'Test Project 1 Munich'
    327 'Vergabeeinheit 10'
    90 'Vergabeeinheit 30'
    91 'Vergabeeinheit 41'
    694 'Vergabeeinheit 733'
    """
    projekte = client.hole_projekte()
    for p_id in (327, 90, 91, 694):
        projekt, = [p for p in projekte if p.id == p_id]
        # "projekte" behält die Verfügbaren

        # Messungen
        datei = "src/data/data.csv"
        client.exportiere_messungen(
            von="01.09.2019",
            bis="14.09.2026",
            projekt=projekt,
            export_datei=datei,
        )

        # Aus Messungen, 
        # Finde eindeutige im Projekt
        eindeutige = hole_eindeutig_und_sortiert_speichern(datei)

        # Hole ROKs

        # in SQLite speichern

    bezeichnungen = read_bezeichnungen(Path("bezeichnungen2read.txt"))
    df = get_messungen(bezeichnungen)
    save_measurements(df)


if __name__ == "__main__":
    main()
