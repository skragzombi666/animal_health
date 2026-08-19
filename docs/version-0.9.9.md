# Animal Health 0.9.9

0.9.9 korrigiert zwei konkrete Bedienungsfehler aus 0.9.8: Pull-to-refresh wurde im Home-Assistant-WebView nicht gebunden, und virtuelle vergangene Serientermine waren im Kalender zwar gelb markiert, aber nicht ausführbar.

## Pull-to-refresh

- Die Gestenlistener werden nicht mehr über einen nachträglich überschriebenen `connectedCallback` registriert.
- Die Registrierung erfolgt beim tatsächlichen Rendern am Panel-Host und damit auch im Home-Assistant-Android-WebView zuverlässig.
- Touch-Ereignisse werden in der Capture-Phase erfasst; die vertikale Geste kann dadurch vor dem übergeordneten Scrollcontainer verarbeitet werden.
- Pull-to-refresh startet nur am oberen Rand, bei einer einzelnen vertikalen Berührung und ohne geöffneten Dialog.
- Die Auslöseschwelle wurde geringfügig reduziert.

## Vergangene Serientermine im Kalender

- Gelbe Einträge «Vergangen, nicht bestätigt» sind jetzt immer als Schaltfläche ausführbar.
- Fehlt der konkrete Termin im aktuell geladenen Dashboard-Ausschnitt, lädt Animal Health ihn gezielt über den bestehenden Dienst `list_task_occurrences` für die gewählte Serie und das gewählte Datum.
- Der geladene Termin wird in den lokalen Panelzustand übernommen und anschließend im normalen Ausführungsdialog geöffnet.
- Bereits geladene gelbe und blaue Termine verwenden weiterhin direkt ihre vorhandene Termin-ID.

## Release

- 0.9.9 ist ein regulärer Home-Assistant/HACS-Release ohne Android-Build.
- Die Android-App bleibt auf 0.9.0-alpha.7 eingefroren.
