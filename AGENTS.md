# Agentenhinweise

## Zweck

Dieses Repository definiert ausschließlich das öffentliche Konvergenzprotokoll und dessen zustandslose Referenzauswertung.

## Invarianten

- Keine Datenbank, Queue oder dauerhafte Laufzeit.
- Keine GitHub-, Bureau-, Grabowski-, Deployment- oder Dateisystemmutation aus der Referenzauswertung.
- Keine Netzwerkzugriffe während einer Auswertung.
- Gleiche Eingaben müssen bytegleiche Ergebnisse erzeugen.
- Effect Receipt und Verification Receipt dürfen nicht zusammengelegt werden.
- Fehlende oder widersprüchliche Belege werden fail-closed behandelt.
- Neue Statuswerte, Receipt-Arten oder Profilanforderungen benötigen Schema-, Fixture-, Test- und Dokumentationsänderungen.
- Öffentliche Fixtures dürfen keine Secrets, privaten Pfade, internen Hostnamen oder personenbezogenen Betriebsdaten enthalten.

## Prüfung

Vor einer Veröffentlichung mindestens:

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
python -m regelkreis.cli validate-contracts
```

## Zuständigkeitsgrenze

Bureau besitzt Taskstatus. Grabowski besitzt Ausführung und Leases. Systemkatalog besitzt Systemsemantik. Chronik besitzt Ereignisgeschichte. Dieses Repository bewertet ausschließlich, ob die vorgelegten Belege ein definiertes Konvergenzübergangskriterium erfüllen.
