"""
Exportiert Messdaten und ROK-Offsets aus MainOps.

Das Skript meldet sich automatisiert an MainOps an, exportiert die
Messdaten eines Projekts als CSV-Datei und ermittelt anschließend die
zugehörigen Offsets (ROKs) aller enthaltenen Messstellen.

Im Gegensatz zur früheren Umsetzung mittels Web-Scraping werden die
verwendeten HTTP-Endpunkte nun direkt angesprochen. Dadurch ist die
Lösung robuster gegenüber Änderungen am Layout der Weboberfläche und
liefert strukturierte Daten mit geringerem Parsing-Aufwand.

Ausgabe:
    data.csv
        Exportierte Messdaten.

    eindeutige.csv
        Alphabetisch sortierte Liste aller Messstellen.

    rok.csv
        Zugehörige Offsets (ROKs) der Messstellen.

Ursprünglich basierte die Lösung auf Web-Scraping. Inzwischen werden
die von MainOps verwendeten HTTP-Endpunkte direkt angesprochen,
wodurch die Implementierung robuster, schneller und weniger anfällig
gegenüber Änderungen der Benutzeroberfläche ist.
"""

import datetime
import logging
import os
import random
import sys
import time
from io import StringIO

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup

from src.mainops.models import MainOpsState, Projekt, Zugangsdaten 
from src.utils.retry import mit_retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log = logging.getLogger(__name__)

EMAIL = os.getenv("USERNAME", "")
PASSWORD = os.getenv("PASSWORD", "")


class MainOpsClient:
    """
    HTTP-Client für den Zugriff auf MainOps.

    Der Client kapselt Anmeldung, Projektauswahl, Export von Messdaten
    sowie die Abfrage von Offsets (ROKs). Hierbei werden die von der
    MainOps-Webanwendung verwendeten HTTP-Endpunkte direkt angesprochen
    und die Antworten automatisiert verarbeitet.

    Attributes
    ----------
    zugangsdaten : Zugangsdaten
        Anmeldedaten für MainOps.

    session : requests.Session
        Persistente HTTP-Sitzung mit Cookie-Verwaltung.

    session_token : str | None
        Anti-Forgery-Token der Anmeldeseite.

    offset_token : str | None
        Anti-Forgery-Token für Offset-Abfragen.
    """

    def __init__(self, zugangsdaten):
        self.zugangsdaten = zugangsdaten
        self.base_url = "https://hj-mainops.com"

        self.session: requests.Session
        self.session_token = None
        self.session_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        }

        self.messstellen = set()
        self.projekte = set()
        self.messungen = []
        self.bezugshoehen = []

        self.offset_token = None

    @property
    def state(self) -> MainOpsState:
        return MainOpsState(
            projekte=self.projekte,
            messungen=self.messungen,
            messstellen=self.messstellen,
            bezugshoehen=self.bezugshoehen,
        )

    def starte_session(self):
        self.session = requests.Session()
        self.session.headers.update()
        self.session.verify = False

        # Anmeldeseite
        r = self.session.get("https://hj-mainops.com/Account/Login")

        # Extrahiere anti-forgery token
        soup = BeautifulSoup(r.text, "html.parser")

        resp = soup.find("input", {"name": "__RequestVerificationToken"})

        if not resp:
            log.info("Kein Token!")
            sys.exit(1)

        self.session_token = resp["value"]

    def anmelden(self):
        payload = {
            "Email": self.zugangsdaten.email,
            "Password": self.zugangsdaten.passwort,
            "RememberMe": "false",
            "__RequestVerificationToken": self.session_token,
        }

        _ = self.session.post(
            "https://hj-mainops.com/Account/Login",
            data=payload,
            allow_redirects=True,
        )

        log.info("\t[Cookies nach Anmeldung]")
        for c in self.session.cookies:
            log.info(f"\t{c.name!r:<40} {c.value!r:.20}...")

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

        if pd.isna(df.iloc[-1, 1]):
            print(1)

        self.messungen.append(df)

    def ermittle_messstellen(self):
        messstellen = list(self.messungen.name.unique())
        messstellen.sort()
        self.messstellen = messstellen

    @staticmethod
    def to_mainops_date(date_str: str) -> str:
        """
        DD.MM.YYYY -> 20-Jul-2026
        """
        return datetime.datetime.strptime(date_str, "%d.%m.%Y").strftime("%d-%b-%Y")

    @staticmethod
    def polite_sleep():
        time.sleep(random.uniform(0.8, 2.2))

    def get_offsets_token(self):

        if self.offset_token:
            return self.offset_token

        response = self.session.get(
            f"{self.base_url}/Offsets",
        )

        soup = BeautifulSoup(response.text, "html.parser")

        self.offset_token = soup.find("input", {"name": "__RequestVerificationToken"})[
            "value"
        ]

        return self.offset_token

    def hole_offsets(self) -> pd.DataFrame:
        for m in self.messstellen:
            mit_retry(self.hole_offsets_je_messstelle, m)

        self.bezugshoehen = pd.concat(self.bezugshoehen)

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

        self.bezugshoehen.append(df)
