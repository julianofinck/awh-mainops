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
import os
import sys
from dataclasses import dataclass
import datetime
from pathlib import Path
import time
import random
import urllib3

import requests
from bs4 import BeautifulSoup
import pandas as pd

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

EMAIL = os.getenv("USERNAME", "")
PASSWORD = os.getenv("PASSWORD", "")

@dataclass
class Zugangsdaten:
    email: str
    passwort: str

@dataclass
class Projekt:
    id: int
    name: str

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

        self.offset_token = None

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
            print("Kein Token!")
            sys.exit(1)

        self.session_token = resp["value"]

    def anmelden(self):
        payload = {
            "Email": self.zugangsdaten.email,
            "Password": self.zugangsdaten.passwort,
            "RememberMe": "false",
            "__RequestVerificationToken": self.session_token,
        }

        r = self.session.post(
            "https://hj-mainops.com/Account/Login",
            data=payload,
            allow_redirects=True,
        )

        print("\n\t[Cookies nach Anmeldung]\n")
        for c in self.session.cookies:
            print(f"\t{c.name!r:<40} {c.value!r:.20}...")
        print("\n")

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

            projekte.append(
                Projekt(
                    id=int(value),
                    name=option.get_text(strip=True)
                )
            )

        return projekte

    def exportiere_messungen(self, von: str, bis: str, projekt: Projekt, export_datei="data.csv"):
        export_payload = {
            "projectNumber": projekt.id,
            "Delimiter": ";",
            "startDate": self.to_mainops_date(von),
            "endDate": self.to_mainops_date(bis),
            "ForScada": "false",
            "AddRaw": "false",
        }

        r = self.session.post(
            "https://hj-mainops.com/Meas/exportData/data.csv",
            data=export_payload,
        )

        print(r.status_code)

        with open(export_datei, "wb") as f:
            f.write(r.content)

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

        self.offset_token = soup.find(
            "input",
            {"name": "__RequestVerificationToken"}
        )["value"]

        return self.offset_token

    def get_offsets(self, messstelle: str, filterchoice: str = "") -> pd.DataFrame:
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
        print(f"\nRequesting {messstelle!r}...")
        self.polite_sleep()

        token = self.get_offsets_token()

        payload = {
            "filterchoice": filterchoice,
            "searchstring": messstelle,
            "__RequestVerificationToken": token,
        }

        response = self.session.post(
            f"{self.base_url}/Offsets/combsearch",
            data=payload,
        )
        response.raise_for_status()

        from io import StringIO
        tables = pd.read_html(StringIO(response.text))

        if not tables:
            return pd.DataFrame()

        EXPECTED_COLUMNS = {
            "Offset",
            "Project",
            "Measurement Point",
        }

        # Fehler wenn mehrere
        df, = [df for df in tables if EXPECTED_COLUMNS.issubset(set(df.columns))]

        # remove action columns
        c2drop = [c for c in df.columns if "Unnamed" in c]
        df = df.drop(columns=c2drop, errors="ignore")

        df.columns = [
            "Offset",
            "Projekt",
            "Messstelle",
            "Anfangsdatum",
            "Kommentar",
            "DoneBy",
        ]


        return df


def hole_eindeutig_und_sortiert_speichern(datei):
    df = pd.read_csv(datei, sep=";")

    # Sortieren
    df = (
        df.assign(DateMeasured=pd.to_datetime(df["DateMeasured"]))
        .sort_values("DateMeasured", ascending=False)
        .reset_index(drop=True)
    )
    df.to_csv(datei, sep=";", index=False)

    eindeutige = list(df.MonitorPoint.unique())
    eindeutige.sort()


    pd.DataFrame(
        {"Bezeichnung": eindeutige}
        ).to_csv(Path(datei).parent / "eindeutige.csv", sep=";", index=False)

    return eindeutige


def main():
    zugangsdaten = Zugangsdaten(EMAIL, PASSWORD)
    client = MainOpsClient(zugangsdaten)
    client.starte_session()
    client.anmelden()

    # Alle Messungen
    projekte = client.hole_projekte()
    auswahl = None
    while auswahl not in [p.id for p in projekte]:
        print(f"\nWelches Projekt?")
        for p in projekte:
            print(f"{p.id:4} '{p.name}'")
        auswahl = int(input("\nAuswahl: "))

    projekt, = [p for p in projekte if "Vergabeeinheit 733" in p.name]

    # Messungen
    datei = "src/data/data.csv"
    client.exportiere_messungen(
        von="01.09.2019",
        bis="14.09.2026",
        projekt=projekt,
        export_datei=datei,
    )

    # Finde eindeutige im Projekt
    eindeutige = hole_eindeutig_und_sortiert_speichern(datei)

    # Hole ROKs (offsets)
    dfs = []
    for gwm in eindeutige:
        dfs.append(client.get_offsets(gwm))

    df = pd.concat(dfs)
    df["Anfangsdatum"] = (
        pd.to_datetime(
            df["Anfangsdatum"],
            format="%m/%d/%Y %I:%M:%S %p"
        )
        .dt.strftime("%d.%m.%Y %H:%M:%S")
    )
    df["Offset"] = (
        pd.to_numeric(df["Offset"])
        .map(lambda x: f"{x:.2f}".replace(".", ","))
    )

    df.to_csv(
        Path(datei).parent / "rok.csv",
        sep=";",
        index=False,
    )

    print(1)

if __name__ == "__main__":
    ti = datetime.datetime.now()
    main()
    tf = datetime.datetime.now()
    print("Zeit:", int((tf - ti).total_seconds()), "s")
