# Animal Health 0.9.35

Version 0.9.35 korrigiert die in 0.9.34 verschlechterte Darstellung von Medikamentengaben in der Chronik.

## Ursache

Die neue Chronikkomponente aus 0.9.34 verwendete mehrere `span`-Elemente innerhalb eines gemeinsamen Textflusses. Eine ältere globale Regel der Basiskomponente setzt jedoch sämtliche `span`-Elemente innerhalb einer Zeile auf `display: block`. Dadurch wurden Tiername, Trennzeichen, Mengenangabe und Metadaten jeweils als eigene Blockzeilen dargestellt. Besonders die nur aus Leerzeichen bestehenden Trennzeichen erzeugten grosse leere Abstände.

## Korrektur

- Medikamentenzeilen bestehen aus genau zwei Layoutspalten: Symbol und Textinhalt.
- Tiername, Mengenangabe, Medikamententitel, Aufgabenherkunft und Sekundärangaben bleiben innerhalb eines einzigen natürlichen Inline-Textflusses.
- Ein Umbruch erfolgt ausschliesslich aufgrund der tatsächlich verfügbaren Breite.
- Trennzeichen erzeugen keine eigenen Zeilen mehr.
- Das Symbol «Aus Aufgabe» bleibt ein kleines Inline-Element direkt hinter dem Titel.
- Nur eine echte Notiz wird unterhalb des Textflusses als separate Zeile dargestellt.
- Die Korrektur gilt gemeinsam für Startseite, Tieransicht, Gesamtchronik und Medikamenteneinträge innerhalb aufgeklappter Behandlungspläne.

## Versionsstand

- Home Assistant/HACS: **0.9.35**
- Android bleibt bei **0.9.0-alpha.7** und übernimmt die Korrektur über das gemeinsame Frontend-Bundle.
