from io import StringIO

import pandas as pd

EXPECTED_COLUMNS = {
    "Offset",
    "Project",
    "Measurement Point",
}


def parse_offsets_html(
    html: str,
) -> pd.DataFrame:

    tables = pd.read_html(StringIO(html))

    if not tables:
        return pd.DataFrame()

    candidates = [df for df in tables if EXPECTED_COLUMNS.issubset(set(df.columns))]

    if not candidates:
        return pd.DataFrame()

    df = candidates[0]

    drop_cols = [c for c in df.columns if "Unnamed" in str(c)]

    df = df.drop(
        columns=drop_cols,
        errors="ignore",
    )

    df.columns = [
        "bezugshoehe",
        "projekt_name",
        "messstelle",
        "ab_zeitpunkt",
        "kommentar",
        "von",
    ]

    df["bezugshoehe"] = pd.to_numeric(
        df["bezugshoehe"],
        errors="coerce",
    )

    df["ab_zeitpunkt"] = pd.to_datetime(
        df["ab_zeitpunkt"],
        format="%m/%d/%Y %I:%M:%S %p",
        errors="coerce",
    )

    return df
