# Animal Health 0.9.0-alpha.3

0.9.0-alpha.3 behebt den Startfehler der Standalone-Android-App aus 0.9.0-alpha.2.

## Behoben: gemeinsame Oberfläche lädt nicht

Die Animal-Health-Frontend-Dateien sind technisch Teilstücke eines einzigen JavaScript-Programms. In 0.9.0-alpha.2 wurden diese 40 Teilstücke unter Android fälschlicherweise einzeln als `<script>` geladen. Da bereits `part01` mitten in der Klassendefinition endet, konnte der WebView das Frontend nicht registrieren und zeigte nur «Die gemeinsame Oberfläche konnte nicht geladen werden».

Ab 0.9.0-alpha.3 werden beim Android-Build alle 40 Frontend-Teile in derselben Reihenfolge wie in der Home-Assistant-Integration zu **einer** `animal-health-panel.js` zusammengefügt. Der WebView lädt nur noch dieses fertige Bundle.

Damit bleibt die Zielarchitektur unverändert: Home Assistant und Android verwenden denselben Animal-Health-Frontend-Code; Android erhält keine separat nachgebaute Oberfläche.

## Regressionstest

Die Android-Tests prüfen nun ausdrücklich, dass die einzelnen Frontend-Teile nicht als separate Skripte geladen werden und dass das zusammengesetzte Frontend syntaktisch gültig ist.
