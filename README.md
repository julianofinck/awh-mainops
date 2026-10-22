# AWH MainOps Export

Dieses Projekt dient dem Export von Messdaten und Bezugshöhen aus MainOps in eine lokale SQLite-Datenbank zur weiteren Auswertung mit SQL, Python oder Excel.

## Ziel

Die MainOps-Weboberfläche eignet sich gut für die tägliche Arbeit, ist jedoch nur eingeschränkt für größere Auswertungen geeignet.

Dieses Projekt überführt die Daten in eine relationale SQLite-Datenbank und ermöglicht dadurch solche Analyse.

## Hintergrund

Die Daten werden ausschließlich über die in MainOps verfügbaren Export-Routen abgerufen. Das Projekt verwendet keine offiziell dokumentierte API und basiert auf der Analyse des Webverkehrs der MainOps-Webanwendung.

## Einschränkungen

### Abhängigkeit von MainOps und fehlende Bearbeiterinformationen

Das Projekt verwendet keine offiziell dokumentierte MainOps-API, sondern basiert auf der Analyse der von der MainOps-Webanwendung verwendeten Exportfunktionen und Requests.

Daher besteht eine starke Abhängigkeit von den aktuell verwendeten MainOps-Endpunkten. Änderungen an URLs, Parametern, Antwortformaten oder Authentifizierungsverfahren können dazu führen, dass der Datenabruf nicht mehr funktioniert und Anpassungen am Code erforderlich werden.

Eine weitere Einschränkung besteht darin, dass die Exportdaten aktuell keine Information darüber enthalten, welcher Benutzer eine Messung durchgeführt oder eingetragen hat. Für Messungen ist daher keine Zuordnung zu einem Bearbeiter möglich.

Für Bezugshöhenänderungen werden die Bearbeiterinformationen hingegen mitgeliefert und in der Datenbank gespeichert.

## Bekannte Annahmen

Das Projekt geht derzeit von folgenden Annahmen aus:

- Messstellennamen sind innerhalb eines Projekts eindeutig.
- Projekte mit dem Präfix `Vergabeeinheit` sind die relevanten Projekte.
- Die Exportdaten von MainOps enthalten vollständige Messwerte und Kommentare.
- Bezugshöhenänderungen werden über die aktuell verwendeten MainOps-Seiten bereitgestellt.

Ändert sich eine dieser Annahmen, kann eine Anpassung der Datenaufbereitung erforderlich werden.

## Ablauf

### 1. Anmeldung

Das Skript meldet sich mit den in der `.env` hinterlegten Zugangsdaten bei MainOps an.

### 2. Projekte laden

Es werden sämtliche verfügbaren Projekte geladen.

Berücksichtigt werden derzeit nur Projekte, deren Name den Text

```text
Vergabeeinheit
```

enthält.

### 3. Messungen abrufen

Anschließend werden sämtliche Messungen im definierten Zeitraum abgerufen.

Standardmäßig:

```text
01.09.2019 bis heute
```

Die Messungen enthalten unter anderem:

- Zeitstempel
- Projekt
- Messstelle
- Messwert in m
- Messwert in m ü. NN
- Bezugshöhe
- Kommentar

### 4. Messstellen bestimmen

Aus den Messdaten werden alle vorhandenen Messstellen ermittelt.

### 5. Bezugshöhen laden

Für jede Messstelle werden die verfügbaren Bezugshöhen geladen.

Dabei werden historische Änderungen der Bezugshöhen berücksichtigt.

### 6. Relationales Modell erzeugen

Die Rohdaten aus MainOps werden in normalisierte Tabellen überführt:

- `projekt`
- `benutzer`
- `messstelle`
- `bezugshoehe`
- `messung`

Textuelle Verweise werden dabei durch Fremdschlüssel ersetzt.

### 7. Import nach SQLite

Die aufbereiteten Daten werden in die SQLite-Datenbank geschrieben.

Vor jedem Import werden die bestehenden Datensätze gelöscht und vollständig neu aufgebaut.

## Laufzeit

Die Gesamtlaufzeit wird im Wesentlichen durch den Abruf der Bezugshöhen bestimmt.

Ein typischer Lauf (Stand Oktober 2026) benötigt:

- Messungen laden: ca. 5 Minuten
- Bezugshöhen laden: ca. 30 Minuten
- Datenaufbereitung und SQLite-Import: wenige Sekunden

Die tatsächliche Laufzeit hängt von der Anzahl der Messstellen und der Antwortzeit von MainOps ab.

## Warum dauern die Bezugshöhen deutlich länger?

Die Messungen können projektweise über die MainOps-Exportfunktion geladen werden.

Für Bezugshöhen existiert dagegen keine vergleichbare Sammelabfrage. Die Daten müssen für jede einzelne Messstelle separat abgefragt werden.

Dadurch entstehen mehrere hundert bis über tausend HTTP-Anfragen pro Lauf.

Um die Systeme von Hoelscher Danmark nicht unnötig zu belasten, wurden bewusst verschiedene Schutzmaßnahmen eingebaut:

- sequentielle Verarbeitung der Anfragen
- kurze Wartezeiten zwischen Requests
- kein paralleler Abruf
- Wiederverwendung bestehender Sessions und Cookies

Dadurch erhöht sich die Laufzeit, das Risiko einer Überlastung oder temporären Sperrung des MainOps-Servers wird jedoch reduziert.

## Datenbankschema

```text
projekt
   │
   └── messstelle
          │
          ├── messung
          │
          └── bezugshoehe
                  │
                  └── benutzer
```

### projekt

Enthält die importierten Vergabeeinheiten.

### benutzer

Enthält die Benutzer, die Bezugshöhenänderungen vorgenommen haben.

### messstelle

Enthält alle Messstellen inklusive Zuordnung zum Projekt.

### bezugshoehe

Historie aller Bezugshöhenänderungen.

### messung

Alle aus MainOps exportierten Messwerte.

## SQL-Ansichten

Die Datenbank stellt zusätzliche Ansichten zur Verfügung.

### v_messstellen

Liste aller Messstellen mit Projektzuordnung.

### v_aktuelle_bezugshoehen

Die letzte Messung, die aktuelle Bezugshöhe, und seit wann die Bezugshöhe je Messstelle.

### v_letzte_messung

Neueste verfügbare Messung