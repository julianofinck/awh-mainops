import sqlite3
from pathlib import Path

import pandas as pd


class DatenbankHandler:
    def __init__(self, db_path, db_neustart=False):
        self.db_path = Path(db_path)
        self.conn: sqlite3.Connection = None
        self.cursor: sqlite3.Cursor = None

        if db_neustart:
            self.db_neu_initialisieren()

        # Connection
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON")

        if not self.cursor:
            self.cursor = self.conn.cursor()

    def db_neu_initialisieren(self):
        # DB völlig entfernen
        if self.db_path.exists():
            self.db_path.unlink()

        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")

        self.cursor = self.conn.cursor()

        for sql_datei_pfad in (
            "schema.sql",
            "ansichten.sql",
        ):
            sql_datei_pfad = "src/database/sql" / Path(sql_datei_pfad)

            with open(sql_datei_pfad, "r", encoding="utf-8") as f:
                self.conn.executescript(f.read())
                self.conn.commit()


def save_measurements(df: pd.DataFrame, db_path: str = "measurements.db"):
    """
    Save a DataFrame of measurements to SQLite.
    Updates existing rows if Zeitpunkt + Messstelle already exists.

    df must have columns:
        ["Messung", "Kommentar", "Neuer Kommentar", "Zeitpunkt", "Messstelle", "Projekt"]
    """

    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if not exists, with UNIQUE constraint
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Messung TEXT,
        Kommentar TEXT,
        Neuer_Kommentar TEXT,
        Zeitpunkt TEXT,
        Messstelle TEXT,
        Projekt TEXT,
        UNIQUE(Zeitpunkt, Messstelle)
    )
    """)
    conn.commit()

    # Insert/update each row
    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO measurements 
            (Messung, Kommentar, Neuer_Kommentar, Zeitpunkt, Messstelle, Projekt)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(Zeitpunkt, Messstelle) DO UPDATE SET
                Kommentar=excluded.Kommentar,
                Neuer_Kommentar=excluded.Neuer_Kommentar,
                Messung=excluded.Messung,
                Projekt=excluded.Projekt
        """,
            (
                row["Messung"],
                row["Kommentar"],
                row["Neuer Kommentar"],
                row["Zeitpunkt"],
                row["Messstelle"],
                row["Projekt"],
            ),
        )

    conn.commit()
    conn.close()
