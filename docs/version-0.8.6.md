# Animal Health 0.8.6

0.8.6 überarbeitet die KI-Mehrfacherfassung, ergänzt kontextspezifische KI-Erfassung und beschleunigt den Wechsel aus der Tierübersicht in die Tierdetailansicht.

## KI-Mehrfacherfassung

Die bisherige Navigation `Eintrag 1 / n` wurde durch eine kompakte, scrollbare Übersichtsansicht ersetzt.

- Jeder erkannte Eintrag erscheint als kompakte Zeile mit Tier, Kurzinhalt und Datum/Zeit.
- Details können direkt unter dem jeweiligen Eintrag auf- und zugeklappt werden.
- Die Statusanzeige unterscheidet klar:
  - graues Fragezeichen: KI unsicher oder Eintrag unvollständig,
  - blaues Häkchen: KI-Erkennung vollständig und mit hoher Sicherheit, aber noch nicht manuell geprüft,
  - grünes Häkchen: manuell geprüft.
- Nach einer manuellen Änderung wird der grüne Prüfstatus wieder aufgehoben.
- Einträge können kompakt über einen roten Papierkorb verworfen bzw. wieder aufgenommen werden.
- Einzelnes Speichern und Sammelspeichern verwenden kompakte Disketten-Symbole.
- Gespeichert werden nur explizit manuell geprüfte und vollständige Einträge.

Oberhalb der Liste steht zusätzlich **Für alle Einträge** zur Verfügung. Datum, Zeit und Notiz können dort gemeinsam auf alle noch aktiven Entwürfe angewendet und danach pro Eintrag weiterhin individuell korrigiert werden.

## Kontextbezogene KI-Erfassung

Neben der allgemeinen KI-Erfassung stehen nun direkte KI-Aktionen in den fachlichen Erfassungsmasken zur Verfügung:

- Gewicht,
- Medikament / Supplement,
- Symptom.

Bei einem einzelnen Ergebnis wird der erkannte Entwurf direkt in das jeweilige Formular übernommen. Mehrere Ergebnisse wechseln in die kompakte Mehrfachprüfung. Die KI bleibt ausschliesslich Erfassungshilfe: Sie speichert nicht selbständig, stellt keine Diagnose und berechnet keine Dosis.

Für die kontextspezifische Analyse wurde `animal_health/v086/ai/analyze` ergänzt. Der Symptommodus unterstützt zusätzlich die strukturierten Felder `symptom` und `severity`.

## Reaktivere Tieransicht

Der Wechsel aus der Tierübersicht in die Detailansicht wurde entkoppelt:

- der erste Klick wechselt unmittelbar sichtbar in die Tieransicht,
- bereits vorhandene Tierstammdaten werden sofort dargestellt,
- Detaildaten und Chronik werden danach geladen,
- Anhänge werden separat und nicht blockierend nachgeladen,
- Profilbilder der Übersicht verwenden nur die komprimierte Thumbnail-Variante und werden nicht mehr als grosse Profilvorschau vor dem Seitenaufbau geladen,
- kleine Tierbilder werden in Übersicht und Navigation auf etwa 50 × 50 Pixel dargestellt sowie lazy/asynchron decodiert,
- Originalbilder und grosse Dokumentvorschauen werden weiterhin erst bei ausdrücklichem Öffnen geladen.

## Prüfstatus-Fix

Einträge gelten nach der KI-Erkennung nicht mehr automatisch als manuell geprüft. Damit hat die manuelle Bestätigung eine eindeutige Funktion und ist Voraussetzung für die Sammelspeicherung.

Zugehörige Issues: #57, #59, #60.
