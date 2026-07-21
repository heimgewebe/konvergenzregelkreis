# Resilienz-Evidence-Profile v2

Status: implementiert für `HEIMGEWEBE-RESILIENZ-V1-T008`.

## Entscheidung

v2 trennt zwei Fragen, die v1 im einzelnen Feld `risk_level` zusammenfasste:

1. **Änderungsrisiko R0–R3:** Wie gefährlich oder schwer reversibel ist die konkrete Änderung?
2. **Zielkritikalität:** Wie kritisch ist das betroffene System laut Systemkatalog für das Gesamtsystem? Zulässig sind `optional`, `supporting`, `essential`, `foundational` und `unknown`.

Die Referenzauswertung wählt deterministisch genau eine der 20 Matrixzellen von `R0-optional` bis `R3-unknown`. Die Profildatei `profiles/resilience.v2.json` wird als Ganzes per SHA-256 an das Ergebnis gebunden.

## Eskalationsregel

Zielkritikalität allein macht eine reversible R1-Änderung nicht zu einer Recovery-Übung. Umgekehrt darf eine riskante Änderung an einem wenig kritischen Ziel nicht automatisch die gleichen Nachweise wie eine kritische Produktionsmutation verlangen.

Zusätzliche Resilienznachweise werden erst für die definierten Kreuzprodukte aktiviert:

- R1 × essential/foundational: Consumer-Kompatibilität und frische Kritikalitätsquelle;
- R1 × foundational: zusätzlich unabhängiges Review;
- R3 bei jeder bekannten Zielkritikalität sowie R2 × essential/foundational: Recovery, begrenzter Degradationsbetrieb, Cleanup und Rückkehr zum Primärpfad;
- R2/R3 × foundational: zusätzlich unabhängige Recovery-Domäne und Common-Mode-Prüfung;
- `unknown`: deterministisch auswählbar, damit Consumer eine stabile Diagnosezelle erhalten; der Status bleibt jedoch fail-closed `blocked`, bis eine kanonische Kritikalität vorliegt;
- bei möglichem Split-Brain: eigener bestandener Negativkontrollbeleg. Diese Anforderung ist bewusst request-abhängig und wird zusätzlich zur statischen Matrixzelle aktiviert.

## Fail-closed-Regeln

Die Auswertung blockiert oder widerspricht, wenn:

- die Kritikalitätsquelle `stale` oder `unknown` ist oder die Zielkritikalität selbst `unknown` bleibt;
- für eine resilienzpflichtige Matrixzelle keine Recovery-Domäne angegeben ist;
- der Degradationsbetrieb nicht ausdrücklich `bounded` ist;
- die Rückkehr zum Primärpfad nicht vorgesehen ist;
- behauptete Unabhängigkeit dieselbe Failure-Domain für Primär- und Recovery-Pfad verwendet;
- behaupteter Same-Domain-Betrieb unterschiedliche Failure-Domains nennt;
- Recovery-, Degradations-, Cleanup- oder Return-to-Primary-Belege fehlen;
- Split-Brain möglich ist, aber der Negativkontrollbeleg fehlt.

## Statuspräzedenz

Die Auswertung ist fail-closed und verwendet für v1 und v2 dieselbe deterministische Präzedenz: `conflicting_evidence` vor `source_stale`, dann `blocked`, dann `evidence_missing`. Erst wenn keine dieser Bedingungen greift, kann eine geschlossene Closure `terminally_closed` ergeben; andernfalls bleibt der Status `transition_allowed`. Ein v2-spezifischer Befund wie `target_criticality: unknown` wird deshalb als Blocker an den gemeinsamen Resolver übergeben, statt die versionsneutrale Statuslogik zu duplizieren.

## Rückwärtskompatibilität

- Alle v1-Schemas, Profile, Fixtures, Statuswerte, Exit-Codes und die Statuspräzedenz bleiben unverändert.
- `evaluate()` dispatcht ausschließlich anhand von `schema_version`.
- Unbekannte Versionen werden als ungültige Eingabe abgewiesen.
- v2 verändert keine Consumerdaten und migriert nichts in-place.

## Migration für Consumer

1. Bestehende v1-Consumer müssen nichts ändern; `schema_version: 1` behält dieselben Schemas, Profile, Statuswerte und Exit-Codes.
2. Ein Consumer optiert explizit mit `schema_version: 2` in die Resilienzklassifikation ein und liefert zusätzlich `target_ref`, die kanonische `target_criticality` sowie die hashgebundene Kritikalitätsquelle.
3. Consumer müssen `profile_id`, `profile_cell_id` und `profile_sha256` als Ergebnisbindung behandeln. Der Profilhash bindet die statische Matrix; request-abhängige Bedingungen wie `split_brain_possible` können darüber hinaus zusätzliche Verifikationen verlangen.
4. `target_criticality: unknown` ist eine Diagnose- und Routingzelle, keine Abschlussfreigabe. Consumer dürfen einen solchen Befund nicht als erfüllbaren Hochrisikoabschluss interpretieren.
5. Unbekannte `schema_version`-Werte sind kein Fallback auf die jüngste bekannte Version, sondern werden fail-closed abgewiesen.

Die aktuelle Paketablage der Vertragsdateien unter `share/konvergenzregelkreis` bleibt in 1.1.x unverändert. Eine mögliche Migration auf paketinterne Ressourcen benötigt einen eigenen Kompatibilitäts- und Installationsvertrag.

## Zuständigkeitsgrenze

Das Protokoll bewertet nur vorgelegte Belege. Es führt keine Recovery aus, bestimmt keine Systemkritikalität, deployt nichts und übernimmt keine Laufzeitwahrheit. Systemkatalog liefert die Kritikalitätsquelle; Grabowski liefert Ausführungs- und Recovery-Belege; Bureau besitzt den Taskstatus; Chronik besitzt die Ereignisgeschichte.


## Bindung an den Systemkatalog

`target_ref`, `target_criticality`, `criticality_source_ref` und `criticality_source_sha256` bilden eine gemeinsame Klassifikationsaussage. Die Namen der Kritikalitäts- und Common-Mode-Klassen entsprechen dem Systemkatalog-Vertrag `catalog/resilience.schema.v1.json`; das Protokoll führt keine zweite Skala ein.
