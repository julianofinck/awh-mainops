from pathlib import Path

from src.data.database import save_measurements
from src.scraper import get_messungen
from src.utils.io import read_bezeichnungen


def main():
    bezeichnungen = read_bezeichnungen(Path("bezeichnungen2read.txt"))
    df = get_messungen(bezeichnungen)
    save_measurements(df)


if __name__ == "__main__":
    main()
