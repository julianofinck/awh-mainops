CREATE VIEW latest_measurements AS
SELECT *
FROM measurements m
WHERE Zeitpunkt = (
    SELECT MAX(Zeitpunkt)
    FROM measurements
    WHERE Messstelle = m.Messstelle
)
ORDER BY Messstelle ASC;
