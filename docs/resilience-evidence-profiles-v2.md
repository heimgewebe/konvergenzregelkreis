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
- `unknown`: deterministisch auswählbar, aber niemals abschließbar;
- bei möglichem Split-Brain: eigener bestandener Negativkontrollbeleg.

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

## Rückwärtskompatibilität

- Alle v1-Schemas, Profile, Fixtures, Statuswerte, Exit-Codes und die Statuspräzedenz bleiben unverändert.
- `evaluate()` dispatcht ausschließlich anhand von `schema_version`.
- Unbekannte Versionen werden als ungültige Eingabe abgewiesen.
- v2 verändert keine Consumerdaten und migriert nichts in-place.

## Zuständigkeitsgrenze

Das Protokoll bewertet nur vorgelegte Belege. Es führt keine Recovery aus, bestimmt keine Systemkritikalität, deployt nichts und übernimmt keine Laufzeitwahrheit. Systemkatalog liefert die Kritikalitätsquelle; Grabowski liefert Ausführungs- und Recovery-Belege; Bureau besitzt den Taskstatus; Chronik besitzt die Ereignisgeschichte.


## Bindung an den Systemkatalog

`target_ref`, `target_criticality`, `criticality_source_ref` und `criticality_source_sha256` bilden eine gemeinsame Klassifikationsaussage. Die Namen der Kritikalitäts- und Common-Mode-Klassen entsprechen dem Systemkatalog-Vertrag `catalog/resilience.schema.v1.json`; das Protokoll führt keine zweite Skala ein.
