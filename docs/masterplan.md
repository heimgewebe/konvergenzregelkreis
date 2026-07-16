# Masterplan `KONVERGENZREGELKREIS-V1`

## Ziel

Systemweite Änderungen werden nicht mit dem Merge gleichgesetzt. Der Regelkreis verbindet Beobachtung, Mutation, Laufzeitwirkung, Produktprüfung und Abschluss durch explizite, hashgebundene Belege.

## Arbeitspakete

| Task | Inhalt | Status im Bootstrap |
|---|---|---|
| T001 | Öffentliches Repo, Lizenz, CI, Security, Agenteneinstieg | umgesetzt |
| T002 | Autoritätsgrenzen und maschinenlesbarer Rollenvertrag | umgesetzt und im Systemkatalog bestätigt |
| T003 | Leitwerk-Abgrenzung und Consumer-Audit | umgesetzt; Fleet und zwei Consumer geprüft |
| T004 | Konvergenzprotokoll v1 | umgesetzt |
| T005 | Evidence-Profile R0–R3 | umgesetzt |
| T006 | Zustandslose Referenzauswertung | umgesetzt |
| T007 | Pilot Systemkatalog-Drift | terminal geschlossen; öffentliche R2-Fixture vorhanden |
| T008 | Pilot Merge bis Deployment | Integrationsvertrag vorhanden; Live-Pilot ausstehend |
| T009 | Bureau- und Grabowski-Integration | erster Abschluss belegt; Adapter bleiben in Eigentümer-Repos |
| T010 | Lebenszyklusabschluss und Cleanup | Bureau, Chronik und Worktree-Archivierung im Pilot belegt |
| T011 | Öffentliche Version 1.0 | nach zwei Live-Piloten und Konfliktfall |

## Releasekriterien für 1.0

- zwei unabhängige Consumer;
- ein vollständiger Merge-Deployment-Live-Abschluss;
- ein belegter Konfliktfall;
- null automatisch falsch geschlossene Vorgänge;
- stabile Semver- und Migrationsregeln;
- öffentliche Fixtures ohne private Betriebsdaten;
- bestätigte Autoritätsgrenzen im Systemkatalog.

## Abbruchkriterien

Die Initiative wird neu bewertet, wenn:

- der Regelkreis eigenen Task- oder Runtimezustand benötigt;
- Consumer regelmäßig externe Belegwahrheit mit Protokollgültigkeit verwechseln;
- R0/R1-Gates messbar mehr Reibung als Nutzen erzeugen;
- ein bestehender Truth Owner durch den Regelkreis verdrängt wird.
