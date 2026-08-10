# Animal Health 0.8.1

0.8.1 konzentriert die Oberfläche auf den operativen Alltag. Das zentrale UX-Ziel lautet: **Was muss ich jetzt tun?** und **Was will ich jetzt dokumentieren?** Häufige Vorgänge sollen in wenigen Taps erledigt sein; Verwaltung und technische Konfiguration bleiben erreichbar, stehen aber nicht im Weg.

## Cleanere Startseite

Die Startseite ist keine Verwaltungsübersicht mehr, sondern eine kompakte Arbeitsfläche:

- Überfällige Aufgaben und alles, was innerhalb der nächsten 24 Stunden fällig ist, wird visuell hervorgehoben.
- Es werden höchstens drei nächste Aufgaben direkt angezeigt. Sind weitere offen, führt `+N weitere` in die vollständige Aufgabenansicht.
- Fällige Aufgaben können direkt von der Startseite ausgeführt werden.
- Ist weniger als drei Mal etwas innerhalb der nächsten 24 Stunden fällig, wird die Vorschau mit den danach nächsten Aufgaben aufgefüllt.
- Die wichtigsten spontanen Erfassungen stehen als grosse Schnellaktionen zur Verfügung: Gewicht, Symptom, Medikament / Supplement, weiterer Chronikeintrag, neue Aufgabe und KI-Dokumenterfassung.
- Die Startseite enthält bewusst keine Export-/Backup-Karten und keine Provider-Auswahl.

## Spontane Medikamenten- und Supplementgabe

`Medikament / Supplement` erlaubt eine einmalige Gabe ohne vorherige Aufgabe:

- Tier auswählen,
- Art `Medikament` oder `Supplement`,
- Produkt, Dosis und Einheit erfassen,
- Applikationsweg, Zeitpunkt und Notiz liegen unter `Weitere Angaben`.

Die Gabe wird direkt als unveränderlicher strukturierter Chronikeintrag gespeichert. Ein Supplement wird dabei rückwärtskompatibel als Medikationsereignis mit dem zusätzlichen Merkmal `product_type=supplement` dokumentiert; es wird kein künstliches Medikament oder keine Aufgabe erzeugt.

## Gewicht korrigieren

Ein Gewichtseintrag kann im Detail über `Gewicht korrigieren` berichtigt werden. Der ursprüngliche Eintrag wird nicht überschrieben oder gelöscht. Stattdessen entsteht ein neuer verknüpfter Korrektureintrag über `correction_of_event_id`.

Die bereits vorhandene rekursive Latest-Weight-Logik berücksichtigt jeweils die wirksame letzte Korrektur. Dadurch verwenden `Aktuelles Gewicht` und die weitere Gewichtshistorie den korrigierten Messwert, während der Audit Trail erhalten bleibt.

## Tiergruppen ohne Einzeltiere

Tiergruppen können in 0.8.1 als eigener fachlicher Bezug verwendet werden. Damit ist eine **Tiergruppen ohne Einzeltiere**-Nutzung möglich, ohne Dummy- oder Sammeltier anzulegen.

- Gruppen können auch mit 0 individuell erfassten Tieren geöffnet und verwendet werden.
- Beobachtungen, Medikation, Impfungen, Behandlung, Pflege, Tierarztbesuche und weitere Einträge können direkt einer Gruppe zugeordnet werden.
- Wiederkehrende und einmalige Aufgaben können direkt für eine Gruppe angelegt werden.
- Gesundheitlich relevante Gruppenaufgaben erzeugen bei der Ausführung einen verknüpften Gruppenchronikeintrag.
- Generische Gruppenerinnerungen können optional in der Gruppenchronik dokumentiert werden.
- Gruppen und Einzeltiere können parallel verwendet werden.
- Gruppen erhalten eine eigene Chronik und einen PDF-Export.
- Portable JSON- und Backup-Exporte nehmen die neuen Gruppentabellen automatisch mit auf, weil sie alle Anwendungstabellen exportieren.

Technisch bleiben Gruppen echte Gruppen: `task_group_targets` verknüpft Aufgaben mit Gruppen; `group_events` speichert die Gruppenchronik. Es wird kein Pseudo-Tier erzeugt.

## KI- und Speech-to-Text-Einstellungen

Die Providerwahl wird aus dem normalen Erfassungsdialog entfernt. Unter `Einstellungen` können eine bevorzugte Home-Assistant-`AI Task`-Entität und eine Speech-to-Text-Entität hinterlegt werden. Der KI-Dokumentassistent verwendet diese Auswahl danach automatisch; wenn keine Auswahl gespeichert ist, bleibt Home Assistants automatische Auswahl aktiv.

Das Diktat übermittelt die aktuelle UI-Sprache ausdrücklich an Speech-to-Text. Für Deutsch wird insbesondere `de-CH` bevorzugt, danach eine tatsächlich unterstützte deutsche Variante wie `de-DE` oder `de`. Die tatsächlich verwendete STT-Sprache wird nach der Transkription angezeigt. Damit soll deutsch gesprochenes Diktat nicht still als Englisch interpretiert werden.

## Verwaltung

Export, Backup und technische KI-Konfiguration befinden sich auf der Einstellungs-/Verwaltungsseite. Gesundheitschronik, Tiere, Aufgaben und Kalender bleiben normale fachliche Ansichten.

Der Grundsatz ist: Auditierbarkeit und Datenportabilität bleiben vollständig erhalten, sind aber im täglichen Dokumentationsworkflow eine Ebene weniger dominant.

## Datenmodell

0.8.1 ergänzt idempotent:

- `v081_settings`
- `group_events`
- `task_group_targets`
- `group_task_configs`

Bestehende Tiere, Tiergruppen, Ereignisse, Aufgaben, Anhänge, Tags und 0.8.0-KI-Daten bleiben unverändert bestehen.

## Praxistest

Vor einem Merge sollen insbesondere folgende Abläufe auf einer realen Home-Assistant-Installation geprüft werden:

- Startseite auf Smartphone: 24-h-Hinweis, drei nächste Aufgaben und direkte Ausführung,
- spontane Medikamenten- und Supplementgabe,
- Tippfehler bei einem Gewicht über `Gewicht korrigieren`,
- reine Tiergruppe mit 0 Einzeltieren: Chronikeintrag, Medikament, Aufgabe, Ausführung und Gruppen-PDF,
- gemischte Tiergruppe aus Gruppen- und Einzeltiereinträgen,
- KI-Dokumenterfassung ohne sichtbare Providerwahl im normalen Dialog,
- deutsches Diktat, insbesondere ein Satz wie `Tina muss hiermit alle 3 Monate entwurmt werden`, mit sichtbarer tatsächlich verwendeter STT-Sprache,
- JSON- und Backup-Export nach Erzeugung gruppenbezogener Daten.

0.8.1 bleibt bis zum erfolgreichen Praxistest auf dem Release-Branch und wird nicht automatisch nach `main` gemergt.
