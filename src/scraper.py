import os
from time import sleep

import pandas as pd
from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv()

# try on this one, if I get error, than call main page and wait login
URL = "https://hj-mainops.com/Meas/Combsearch"
HOMEPAGE = "https://hj-mainops.com"

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")


def read_table(page: Page) -> pd.DataFrame:
    page.wait_for_selector("table.table tbody tr")

    rows = page.query_selector_all("table.table tbody tr")

    data = []

    for row in rows:
        cells = row.query_selector_all("td")

        messung = cells[0].inner_text().strip()
        kommentar = cells[1].inner_text().strip()
        neuer_kommentar = cells[2].inner_text().strip()
        zeitpunkt = cells[3].inner_text().strip()

        # Messstelle ist Button-Text
        messstelle = cells[4].query_selector("button").inner_text().strip()

        projekt = cells[5].inner_text().strip()

        data.append(
            {
                "Messung": messung,
                "Kommentar": kommentar,
                "Neuer Kommentar": neuer_kommentar,
                "Zeitpunkt": zeitpunkt,
                "Messstelle": messstelle,
                "Projekt": projekt,
            }
        )

    df = pd.DataFrame(data)

    return df


def get_messungen(bezeichnungen: list[str]) -> pd.DataFrame:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(HOMEPAGE)

        page.click("button.btn-hoelscher")
        sleep(3)

        page.fill("#Email", USERNAME)
        page.fill("#Password", PASSWORD)

        page.click("button.btn.btn-hoelscher")

        page.goto("https://hj-mainops.com/Meas")
        sleep(1)

        all_dfs = list()
        for bezeichnung in bezeichnungen:
            page.fill("#search", bezeichnung)

            page.locator(
                "button.btn-hoelscher",
            ).filter(has=page.locator("span.glyphicon-search")).click()

            df = read_table(page)

            all_dfs.append(df)

        browser.close()

    # Single df
    df = pd.concat(all_dfs)

    # ISO date string
    df["Zeitpunkt"] = pd.to_datetime(
        df["Zeitpunkt"], format="%d-%b-%Y %H:%M"
    ).dt.strftime("%Y-%m-%d %H:%M:%S")

    return df
