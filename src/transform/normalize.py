import pandas as pd

NAME_MAPPING = {
    "?BR": "ÜBR",
    "Leitf?higkeit": "Leitfähigkeit",
    "w?sserung": "wässerung",
    "Tr?bung": "Trübung",
    "stra?e": "straße",
}


def korrigiere_messstellennamen(df: pd.DataFrame) -> pd.DataFrame:
    """
    Korrigiert bekannte Encodingfehler in Messstellennamen.
    """
    df = df.copy()

    for falsch, richtig in NAME_MAPPING.items():
        df["name"] = df["name"].str.replace(
            falsch,
            richtig,
            regex=False,
        )

    return df


def sortiere_messungen(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sortiert Messungen nach Zeitstempel.
    """
    return df.sort_values(
        by="zeitpunkt",
        ascending=False,
    )


def ermittle_messstellen(df: pd.DataFrame) -> list[str]:
    """
    Liefert eindeutige Messstellen.
    """
    messstellen = df["name"]().unique().tolist()

    messstellen.sort()

    return messstellen


def normalize_messungen(df: pd.DataFrame) -> pd.DataFrame:
    """
    Führt alle Standard-Korrekturen für Messungen aus.
    """
    df = korrigiere_messstellennamen(df)
    df = sortiere_messungen(df)

    return df

def ersetze_namen_durch_fremdschluessel(
    dataframe: pd.DataFrame,
    spalte: str,
    referenz_df: pd.DataFrame,
    ziel_spalte: str | None = None,
) -> pd.DataFrame:
    if ziel_spalte is None:
        ziel_spalte = f"{spalte}_id"

    mapping = dict(zip(referenz_df["name"], referenz_df["id"]))

    dataframe[ziel_spalte] = dataframe[spalte].map(mapping)

    dataframe.drop(columns=spalte, inplace=True)

    return dataframe