# Pilot: Grabowski Merge → Deployment → Live

## Zweck

Dieser zweite, vom Systemkatalog-Pilot unabhängige R2-Pilot bindet einen realen Merge an ein unveränderliches Deployment, aktuelle Laufzeitidentität, Dienstgesundheit, einen isolierten Liveprobe sowie Bureau-, Chronik- und Cleanup-Belege.

## Belegter Vorgang

- Pull Request: `heimgewebe/grabowski#235`
- Merge-Commit und Runtime-`repo_head`: `0b09e6d7dfdb0b3171d33d5bd782d37eb36e7134`
- Unveränderlicher Release: `0b09e6d7dfdb-srcsetb0de45d3505d-locke6664d600b6c-contract51062bb6992c`
- CI: Python 3.10 und 3.12 bestanden
- Repository-Validierung: 1.789 Tests bestanden, 1 Test übersprungen
- Bureau: `GRABOWSKI-KILL-SWITCH-RECOVERY-V1-T001` verifiziert
- Chronik: `sha256:3ea06516bfdff77a39d4db66ccf59796f0d34995eb9266241d8a3a10fe1ac44c`
- Cleanup: archivierter Deployment-Worktree `20260716T013659Z-6498c15a1c87`

Die öffentliche Fixture enthält keine privaten Pfade, Tokens, Logs oder Marker-Inhalte.

## Restrisiko

Der Pilot belegt eine starke Operator-Policy-Grenze, aber keine Kernel-Isolation gegen beliebige bereits laufende Prozesse derselben Unix-UID. Dieser Punkt bleibt separat in Bureau-Task `GRABOWSKI-KILL-SWITCH-RECOVERY-V1-T002` offen.

## Konfliktfall

`conformance/conflict/grabowski-pilot-r2-conflicting-deployment.json` ist ein reproduzierbarer Negative-Control-Replay. Er ergänzt zur realen Belegkette eine bewusst divergierende zweite Deployment-Identität. Die Auswertung muss `conflicting_evidence` und Exit-Code 4 liefern, obwohl alle Pflichtbelege und eine geschlossene Closure vorhanden sind.

Der Konfliktfall behauptet nicht, dass das produktive Deployment widersprüchlich war. Er belegt die fail-closed Reaktion des Protokolls auf widersprüchliche Consumer-Eingaben.
