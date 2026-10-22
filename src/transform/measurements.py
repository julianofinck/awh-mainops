import pandas as pd
from .normalize import ersetze_namen_durch_fremdschluessel


def data_verarbeiten(
    state,
) -> pd.DataFrame:

    # Objekte organisieren
    messungen = state.messungen
    messungen.projekt = messungen.projekt.str.replace("Vergabeeinheit ", "VE")
    messstellen = messungen[["projekt", "name"]]

    bezugshoehen = state.bezugshoehen
    bezugshoehen.projekt_name = bezugshoehen.projekt_name.str.replace(
        "Vergabeeinheit ", "VE"
    )

    # PK-Schlüssel & Datensätzen sortieren
    messungen.sort_values(by="zeitpunkt", inplace=True)
    messungen.reset_index(drop=True, inplace=True)
    messungen["id"] = list(range(1, len(messungen) + 1))
    messungen.drop(columns=["ext_monitor_point"], inplace=True)

    projekte = pd.DataFrame({"name": messungen.projekt.unique()})
    projekte.sort_values(by="name", inplace=True)
    projekte["id"] = range(1, len(projekte) + 1)

    benutzer = pd.DataFrame({"name": bezugshoehen.von.dropna().unique()})
    benutzer.sort_values(by="name", inplace=True)
    benutzer["id"] = range(1, len(benutzer) + 1)

    bezugshoehen.sort_values(by="ab_zeitpunkt")
    bezugshoehen["id"] = range(1, len(bezugshoehen) + 1)
    bezugshoehen.rename(columns={"bezugshoehe": "wert"}, inplace=True)

    messstellen = (
        messungen[["name", "projekt"]]
        .drop_duplicates()
        .sort_values(by="name")
        .reset_index(drop=True)
    )
    messstellen["id"] = range(1, len(messstellen) + 1)

    # FK-Schlüssel
    messstellen = ersetze_namen_durch_fremdschluessel(messstellen, "projekt", projekte)
    messungen = ersetze_namen_durch_fremdschluessel(messungen, "projekt", projekte)
    messungen = ersetze_namen_durch_fremdschluessel(
        messungen, "name", messstellen, "messstelle_id"
    )

    bezugshoehen = ersetze_namen_durch_fremdschluessel(
        bezugshoehen, "projekt_name", projekte, "projekt_id"
    )
    bezugshoehen = ersetze_namen_durch_fremdschluessel(
        bezugshoehen, "messstelle", messstellen
    )
    bezugshoehen = ersetze_namen_durch_fremdschluessel(
        bezugshoehen, "von", messstellen, "benutzer_id"
    )

    return (
        projekte,
        benutzer,
        messstellen,
        bezugshoehen,
        messungen,
    )