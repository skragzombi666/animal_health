# Animal Health 0.9.31

## Aussagekräftige Aufgabenkennzahl in der Tieransicht

Die bisherige Kennzahl **«Offene Aufgaben»** basierte auf den in der Tierdetailantwort enthaltenen offenen Aufgabeninstanzen. Eine bereits geplante nächste Ausführung konnte deshalb unter **«Anstehend»** erscheinen, während die Kennzahl gleichzeitig `0` zeigte.

- Die Kennzahl heisst neu **«Aktive Aufgaben»**.
- Gezählt werden aktive, für das Tier relevante Aufgabendefinitionen statt nur aktuell geladener Fälligkeitsinstanzen.
- Wiederkehrende Aufgaben werden genau einmal gezählt, unabhängig von der Zahl ihrer vergangenen oder zukünftigen Ausführungen.
- Gruppenaufgaben und Aufgaben mit Mehrfachziel werden beim jeweiligen Tier berücksichtigt.
- Erledigte einmalige Aufgaben ohne weitere offene Ausführung werden nicht als aktiv gezählt.
- Die Kennzahl ist anklickbar und öffnet direkt die Aufgabenverwaltung des Tiers.

## Aufgabenverwaltung direkt beim Tier

- Rechts im Kopf der Karte **«Anstehend»** befindet sich ein Aufgaben-/Clipboard-Symbol.
- Das Symbol öffnet ein Pop-up mit allen relevanten aktiven und deaktivierten Aufgaben dieses Tiers.
- Das Pop-up zeigt Aufgabenart, Wiederholung, Planwerte und nächste Ausführung.
- Jede Aufgabe kann dort direkt bearbeitet sowie aktiviert oder deaktiviert werden.
- Neue Aufgaben lassen sich aus demselben Pop-up mit bereits vorausgewähltem Tier anlegen.
- Der Bearbeiten-Stift an einer konkret anstehenden Aufgabe bleibt als direkter Schnellzugriff erhalten.

## Detaildarstellung

- In der eigenen Tieransicht wird der Tiername innerhalb einer Aufgabenzeile nicht mehr redundant wiederholt.
- Bei gruppenweiten Aufgaben bleibt stattdessen die Tiergruppe als fachlich relevante Herkunft sichtbar.
- Überschrift und Anzahl einer Fälligkeitsgruppe werden getrennt dargestellt; beispielsweise erscheint **«Morgen 1»** nicht mehr als zusammengeklebtes **«Morgen1»**.

## Release

- Home-Assistant/HACS-Version: **0.9.31**
- Android bleibt unverändert bei **0.9.0-alpha.7**
