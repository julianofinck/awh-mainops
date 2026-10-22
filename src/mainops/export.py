import datetime
import logging

import pandas as pd
from bs4 import BeautifulSoup

from src.mainops.models import Projekt

log = logging.getLogger(__name__)


class MeasurementExporter:

    def __init__(
        self,
        session,
        base_url,
    ):
        self.session = session
        self.base_url = base_url

    def hole_projekte(self) -> list[Projekt]:
        r = self.session.get(
            "https://hj-mainops.com/Offsets",
        )

        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        select = soup.find("select", {"name": "filterchoice"})
        if select is None:
            raise RuntimeError("Projektliste nicht gefunden")

        projekte = []

        for option in select.find_all("option"):
            value = option.get("value")

            if not value or not value.isdigit():
                continue

            projekte.append(Projekt(id=int(value), name=option.get_text(strip=True)))

        return projekte

    def hole_messungen(
        self,
        von: str,
        bis: str,
    ):
        for p in self.projekte:
            log.info(f"\t\tRequesting Messungen - Projekt: {p!r}")

            von_dt = datetime.datetime.strptime(von, "%d.%m.%Y")
            bis_dt = datetime.datetime.strptime(bis, "%d.%m.%Y")

            for year in range(von_dt.year, bis_dt.year + 1):
                von_chunk = max(von_dt, datetime.datetime(year, 1, 1))

                if year == bis_dt.year:
                    bis_chunk = bis_dt
                else:
                    bis_chunk = datetime.datetime(year, 12, 31)

                self.hole_messungen_jahr(
                    von_chunk.strftime("%d.%m.%Y"),
                    bis_chunk.strftime("%d.%m.%Y"),
                    p,
                )

        if self.messungen:
            self.messungen = pd.concat(self.messungen).sort_values(
                by="zeitpunkt",
                ascending=False,
            )

            # Korrigiere "?" encoding
            map_korrekt = {
                "?BR": "ÜBR",
                "Leitf?higkeit": "Leitfähigkeit",
                "w?sserung": "wässerung",
                "Tr?bung": "Trübung",
                "stra?e": "straße",
            }
            for falsch, richtig in map_korrekt.items():
                self.messungen["name"] = self.messungen["name"].str.replace(
                    falsch,
                    richtig,
                    regex=False,
                )

    def hole_messungen_jahr(self, von: str, bis: str, projekt: Projekt):
        log.info(f"\tZeitraum: {von} bis {bis}")

        export_payload = {
            "projectNumber": projekt.id,
            "Delimiter": ";",
            "startDate": self.to_mainops_date(von),
            "endDate": self.to_mainops_date(bis),
            "ForScada": "false",
            "AddRaw": "true",
        }

        response = self.session.post(
            "https://hj-mainops.com/Meas/exportData/data.csv",
            data=export_payload,
        )

        decoded = response.content.decode("utf-8")

        rows = []

        for line in decoded.splitlines():
            rows.append(line.split(";", maxsplit=6))

        df = pd.DataFrame(
            rows,
            columns=[
                "name",
                "zeitpunkt",
                "messwert_nmm",
                "messwert_m",
                "ext_monitor_point",
                "bezugshoehe",
                "kommentar",
            ],
        )

        # NOTE: MainOps liefert concatenated Tabellen; wenn kein mNN, ist ein Header
        # Ignoriere Kopfzeile von MainOps exportierte Flat-Tabelle
        df = df[df["name"] != "MonitorPoint"]
        if df.empty:
            return

        df.columns = (
            "name",
            "zeitpunkt",
            "messwert_nmm",
            "messwert_m",
            "ext_monitor_point",
            "bezugshoehe",
            "kommentar",
        )
        df[c] = pd.to_numeric(df[(c := "messwert_nmm")], errors="coerce")
        df[c] = pd.to_numeric(df[(c := "messwert_m")], errors="coerce")
        df[c] = pd.to_numeric(df[(c := "bezugshoehe")], errors="coerce")
        df[c] = pd.to_datetime(
            df[(c := "zeitpunkt")], format="%Y-%m-%d %H:%M:%S", errors="coerce"
        )
        df["projekt"] = projekt.name

        self.messungen.append(df)
