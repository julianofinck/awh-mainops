import logging
import random
import time
from io import StringIO

import pandas as pd

from src.utils.retry import mit_retry

log = logging.getLogger(__name__)


class OffsetClient:

    def __init__(
        self,
        session,
        base_url,
        auth,
    ):
        self.session = session
        self.base_url = base_url
        self.auth = auth

    @staticmethod
    def polite_sleep():
        time.sleep(random.uniform(0.8, 2.2))

    def hole_offsets(self) -> pd.DataFrame:
        for m in self.messstellen:
            mit_retry(self.hole_offsets_je_messstelle, m)

        self.bezügshöhen = pd.concat(self.bezügshöhen)

    def hole_offsets_je_messstelle(
        self, messstelle_name, filterchoice: str = ""
    ) -> pd.DataFrame:
        """
        Search offsets by measurement point name.


        Parameters
        ----------
        messstelle : str
            e.g. '2S-8/128'
        filterchoice : str, optional
            Project filter id

        Returns
        -------
        pd.DataFrame
        """
        log.info(f"\t\tRequesting Offset: {messstelle_name!r}...")
        self.polite_sleep()

        token = self.get_offsets_token()

        payload = {
            "filterchoice": filterchoice,
            "searchstring": messstelle_name,
            "__RequestVerificationToken": token,
        }

        response = self.session.post(
            f"{self.base_url}/Offsets/combsearch",
            data=payload,
        )
        response.raise_for_status()

        # Extrahire alle Tabelle von HTML
        # die richtige hat gewisse Spalten
        tables = pd.read_html(StringIO(response.text))
        if not tables:
            log.warning("Keine Tabelle")
            return
        EXPECTED_COLUMNS = {
            "Offset",
            "Project",
            "Measurement Point",
        }
        # Zeige Fehler wenn mehrere
        (df,) = [df for df in tables if EXPECTED_COLUMNS.issubset(set(df.columns))]
        if df.empty:
            log.warning("leere Tabelle")
            return

        # remove action columns
        c2drop = [c for c in df.columns if "Unnamed" in c]
        df = df.drop(columns=c2drop, errors="ignore")

        df.columns = (
            "bezugshoehe",
            "projekt_name",
            "messstelle",
            "ab_zeitpunkt",
            "kommentar",
            "von",
        )
        df[c] = pd.to_numeric(df[(c := "bezugshoehe")], errors="coerce")
        df[c] = pd.to_datetime(
            df[(c := "ab_zeitpunkt")], format="%m/%d/%Y %I:%M:%S %p", errors="coerce"
        )

        self.bezügshöhen.append(df)
