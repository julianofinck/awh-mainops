import logging
import sys

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


class MainOpsAuth:

    def __init__(self, zugangsdaten):
        self.zugangsdaten = zugangsdaten

        self.session = None
        self.session_token = None
        self.offset_token = None

        self.base_url = "https://hj-mainops.com"

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

        r = self.session.post(
            "https://hj-mainops.com/Account/Login",
            data=payload,
            allow_redirects=True,
        )

        log.info("\t[Cookies nach Anmeldung]")
        for c in self.session.cookies:
            log.info(f"\t{c.name!r:<40} {c.value!r:.20}...")

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
