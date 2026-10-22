CREATE TABLE IF NOT EXISTS benutzer (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT, -- PG UUID
    name                    TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS projekt (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT, -- PG UUID
    name                    TEXT UNIQUE -- [note: "VE10/VE30/VE41/VE733"]
);

CREATE TABLE IF NOT EXISTS messstelle (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT, -- PG UUID
    name                    TEXT UNIQUE,
    projekt_id              INTEGER,

	FOREIGN KEY (projekt_id) REFERENCES projekt(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messung (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT, -- PG UUID
    messstelle_id           INTEGER,
    projekt_id           INTEGER,
    zeitpunkt               INTEGER, -- PG DATE
    messwert_nmm                    REAL, 
    messwert_m                    REAL, 
    bezugshoehe                    REAL, 
    kommentar               TEXT,

	FOREIGN KEY (messstelle_id) REFERENCES messstelle(id) ON DELETE CASCADE,
	FOREIGN KEY (projekt_id) REFERENCES projekt(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bezugshoehe (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT, -- PG UUID
    messstelle_id           INTEGER,
    benutzer_id             INTEGER,
    projekt_id             INTEGER,
    ab_zeitpunkt            INTEGER, -- PG DATE
    wert                    REAL, 
    kommentar               TEXT,

	FOREIGN KEY (messstelle_id) REFERENCES messstelle(id) ON DELETE CASCADE,
	FOREIGN KEY (benutzer_id) REFERENCES benutzer(id) ON DELETE CASCADE,
	FOREIGN KEY (projekt_id) REFERENCES projekt(id) ON DELETE CASCADE
);
