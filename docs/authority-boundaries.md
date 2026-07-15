# Autoritätsgrenzen

## Eigene Wahrheit

Dieses Repository besitzt ausschließlich:

- Protokollschemas;
- Evidence-Profile;
- Übergangssemantik;
- Konformitätstestvektoren;
- die zustandslose Referenzauswertung.

## Fremde Wahrheit

| Domäne | Autoritative Quelle |
|---|---|
| Systemzweck und Beziehungen | Systemkatalog |
| Fleet-Mitgliedschaft | Metarepo |
| Aufgaben, Abhängigkeiten, Claims und Taskabschluss | Bureau |
| Ausführung, Leases, Audit und Recovery | Grabowski |
| Commit, Pull Request und Merge | GitHub und jeweiliges Repository |
| Deployment und Runtime | jeweiliger Dienst und Deploymentpfad |
| Ereignisgeschichte | Chronik |
| Projektionen | Leitstand und Schauwerk |

## Integrationsregel

Consumer dürfen ein Transition Assessment als **Bewertung eines vorgelegten Evidence-Pakets** verwenden. Sie dürfen daraus nicht ableiten, dass externe Belege wahr, aktuell oder von einer autorisierten Instanz erzeugt wurden, sofern deren eigener Vertrag dies nicht separat beweist.

## Keine zentrale Control Plane

Der Konvergenzregelkreis besitzt keine:

- Datenbank;
- Queue;
- Hintergrundjobs;
- Retry-Logik;
- Secrets;
- Host- oder Deploymentkonfiguration;
- Schreibadapter;
- automatische Merge- oder Abschlussautorität.
