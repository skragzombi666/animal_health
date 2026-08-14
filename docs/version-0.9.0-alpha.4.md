# Animal Health 0.9.0-alpha.4

0.9.0-alpha.4 behebt den Android-Installationskonflikt zwischen aufeinanderfolgenden Alpha-APKs.

## Stabile Alpha-Signatur

Die bisherigen Standalone-APKs wurden als Debug-Build jeweils auf einem frischen GitHub-Runner signiert. Dadurch konnte sich der Debug-Signierschlüssel von Build zu Build ändern. Android behandelt eine APK mit gleicher Paket-ID, aber anderer Signatur nicht als gültiges Update und meldet einen Paketkonflikt.

Ab 0.9.0-alpha.4 verwendet die Android-Alpha einen **festen, ausschließlich für öffentliche Testbuilds vorgesehenen Alpha-Signierschlüssel**. Damit sollen kommende `0.9.0-alpha.x`-APKs normal über eine bestehende Installation aktualisiert werden können.

Der Alpha-Schlüssel ist bewusst kein Produktionsschlüssel und wird später nicht für einen produktiven Store-Release verwendet.

## Einmaliger Übergang

Installationen von 0.9.0-alpha.1 bis 0.9.0-alpha.3 wurden noch mit den vorherigen wechselnden Debug-Schlüsseln gebaut. Deren Signatur kann nicht nachträglich geändert werden. Deshalb muss vor der Installation von 0.9.0-alpha.4 einmalig die bisherige **Animal Health Alpha** deinstalliert werden.

Ab 0.9.0-alpha.4 soll dieser Schritt bei normalen Alpha-Updates nicht mehr erforderlich sein.

## Weiter enthalten

- dieselbe Animal-Health-Oberfläche wie in Home Assistant,
- lokaler Standalone-Backend-Adapter,
- Tiergruppen, Tags, Tiere, Chronik, Aufgaben/Serien, Kalender und Medikamente,
- lokale Anhänge und Exporte,
- die in 0.9.0-alpha.3 korrigierte gebündelte gemeinsame Frontend-Auslieferung.
