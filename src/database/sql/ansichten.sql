-- =====================================================
-- Ansicht: Messstellen
-- =====================================================

CREATE VIEW IF NOT EXISTS v_messstellen AS
SELECT
    p.name AS projekt,
    ms.id AS messstelle_id,
    ms.name AS messstelle
FROM messstelle ms
JOIN projekt p
    ON ms.projekt_id = p.id;


-- =====================================================
-- Ansicht: Aktuelle Bezugshöhe je Messstelle
-- =====================================================

CREATE VIEW IF NOT EXISTS v_aktuelle_bezugshoehen AS
WITH letzte_bezugshoehe AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY messstelle_id
            ORDER BY ab_zeitpunkt DESC
        ) AS rn
    FROM bezugshoehe
)
SELECT
    p.name AS projekt,
    ms.id AS messstelle_id,
    ms.name AS messstelle,
    l.ab_zeitpunkt,
    l.wert
FROM letzte_bezugshoehe l
JOIN messstelle ms
    ON l.messstelle_id = ms.id
JOIN projekt p
    ON ms.projekt_id = p.id
WHERE l.rn = 1;


-- =====================================================
-- Ansicht: Letzte Messung je Messstelle
-- =====================================================

CREATE VIEW IF NOT EXISTS v_letzte_messung AS
WITH letzte_messung AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY messstelle_id
            ORDER BY zeitpunkt DESC
        ) AS rn
    FROM messung
)
SELECT
    p.name AS projekt,
    ms.id AS messstelle_id,
    ms.name AS messstelle,
    l.zeitpunkt,
    l.messwert_nmm,
    l.messwert_m,
    l.bezugshoehe,
    l.kommentar
FROM letzte_messung l
JOIN messstelle ms
    ON l.messstelle_id = ms.id
JOIN projekt p
    ON ms.projekt_id = p.id
WHERE l.rn = 1;


-- =====================================================
-- Ansicht: Aktueller Status je Messstelle
-- =====================================================

CREATE VIEW IF NOT EXISTS v_messstellen_status AS
SELECT
    lm.projekt,
    lm.messstelle,
    lm.zeitpunkt AS letzte_messung,
    lm.messwert_nmm,
    lm.messwert_m,
    lm.bezugshoehe,
    ab.ab_zeitpunkt AS bezugshoehe_seit
FROM v_letzte_messung lm
LEFT JOIN v_aktuelle_bezugshoehen ab
    ON lm.messstelle_id = ab.messstelle_id;