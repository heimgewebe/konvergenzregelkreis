# Integrationsleitfaden

## Grundprinzip

Ein Consumer erzeugt oder sammelt ein `assessment-request.v1`-Dokument und übergibt es unverändert an die Referenzauswertung. Der Regelkreis verändert keine Quelle und löst keine Evidence-Referenz selbst auf.

## Bureau

Bureau bleibt Eigentümer des Tasklebenszyklus. Ein Task darf ein Transition Assessment als Abschlussbeleg referenzieren. Nur `terminally_closed` rechtfertigt einen terminalen Abschluss, sofern Bureau zusätzlich Identität und Autorisierung des Evidence-Pakets prüft.

## Grabowski

Grabowski kann hashgebundene Effect- und Verification-Receipts erzeugen. Der Regelkreis darf Grabowski nicht selbst aufrufen. Die Trennung verhindert, dass der Prüfer seine eigenen Belege erzeugt.

## Systemkatalog

Der Systemkatalog veröffentlicht Rolle und Wahrheitsgrenzen des Regelkreises. Driftbeobachter können eine Observation erzeugen. Semantische Katalogänderungen bleiben proposal-only und benötigen normale Prüfung, Merge- und Consumerbelege.

## Chronik

Chronik kann die Abfolge von Observation, Effect, Verification und Closure festhalten. Chronik ist nicht der Eigentümer des aktuellen Taskstatus.

## Leitstand und Schauwerk

Beide Systeme dürfen Transition Assessments projizieren, aber keine fehlenden Belege erfinden oder einen nichtterminalen Status visuell als abgeschlossen darstellen.

## Pilot: Systemkatalog-Drift

1. Watchdog erzeugt eine hashgebundene Observation.
2. Semantische Klassifikation unterscheidet Quellenneubindung von Rollenänderung.
3. Bureau dedupliziert die Kandidatur.
4. Normaler PR-, Review- und Mergepfad erzeugt Effect Receipts.
5. Manifest-, Leitstand- und Schauwerkprüfungen erzeugen Verification Receipts.
6. Erneuter Driftlauf muss `materialDrift=false` belegen.
7. Cleanup, Bureau und Chronik werden in einem Closure Receipt gebunden.
8. Erst `terminally_closed` beendet den Pilot.
