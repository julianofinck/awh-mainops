import sqlite3

import pandas as pd


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
