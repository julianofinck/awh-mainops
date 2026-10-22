import os

import pandas as pd

from src.database.handler import DatenbankHandler


def speichere_in_sqlite(
    projekt_df: pd.DataFrame,
    benutzer_df: pd.DataFrame,
    messstelle_df: pd.DataFrame,
    bezugshoehe_df: pd.DataFrame,
    messung_df: pd.DataFrame,
) -> None:

    db = DatenbankHandler(
        db_path=os.getenv("DB_PATH", ""),
        db_neustart=os.getenv(
            "DB_NEUSTART",
            "false",
        ).lower()
        == "true",
    )

    conn = db.conn

    with conn:
        # Reihenfolge wichtig wegen Foreign Keys
        conn.execute("DELETE FROM messung")
        conn.execute("DELETE FROM bezugshoehe")
        conn.execute("DELETE FROM messstelle")
        conn.execute("DELETE FROM benutzer")
        conn.execute("DELETE FROM projekt")

        # Stammdaten
        projekt_df.to_sql(
            "projekt",
            conn,
            if_exists="append",
            index=False,
        )

        benutzer_df.to_sql(
            "benutzer",
            conn,
            if_exists="append",
            index=False,
        )

        messstelle_df.to_sql(
            "messstelle",
            conn,
            if_exists="append",
            index=False,
        )

        # Bewegungsdaten
        bezugshoehe_df.to_sql(
            "bezugshoehe",
            conn,
            if_exists="append",
            index=False,
        )

        messung_df.to_sql(
            "messung",
            conn,
            if_exists="append",
            index=False,
            chunksize=1000,
        )
