# Architektur-Inventar

`legacy-baseline.json` ist die maschinenlesbare Referenz der mit Animal Health 0.9.41 eingefrorenen Legacy-Architektur.

Erfasst werden:

- alle 99 nummerierten Frontend-Fragmente mit Grösse und Inhalts-Hashes,
- Prototypüberschreibungen,
- Aktionen, Ansichten und Dialogtypen,
- WebSocket-Commands, Services und Übersetzungsschlüssel,
- die Zahl eingebetteter Style-Blöcke,
- Backend-Patchfunktionen und ihre Registrierungsreihenfolge,
- direkte Runtime-Methodenzuweisungen,
- echte Migrationsmodule und versionsgebundene Runtime-Module.

Die Baseline wird nicht manuell bearbeitet. Sie wird einmalig aus dem Referenzstand erzeugt:

```bash
python scripts/architecture_inventory.py --root . --write
```

Die dauerhafte CI-Prüfung lautet:

```bash
python scripts/architecture_inventory.py --root . --check
```

Die Prüfung erlaubt den späteren Abbau von Prototyp- und Runtime-Patches, aber keine neuen Einträge. Die 99 Legacy-Dateien und ihre Inhalte bleiben bis zu ihrem eigenen, rein technischen Verschiebeschritt exakt eingefroren.

Eine Aktualisierung der Baseline ist nur in einem ausdrücklich als Architektur-Migration abgegrenzten Pull Request zulässig. Ein normaler Feature- oder Bugfix-PR darf die Baseline nicht erweitern.
