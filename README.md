# Konvergenzregelkreis

Öffentliches, zustandsloses Protokoll für den beleggebundenen Abschluss von Änderungen im Heimgewebe.

> Änderung ≠ Wirkung · Merge ≠ Deployment · Deployment ≠ korrekte Laufzeit · Laufzeit ≠ Produktnutzen

Der Konvergenzregelkreis definiert, welche Belege zwischen Beobachtung und systemischem Abschluss erforderlich sind. Er ist **keine Control Plane** und besitzt weder Aufgaben, Leases, Deployments noch Laufzeitstatus.

## Zuständigkeit

Der Konvergenzregelkreis besitzt:

- die Protokollschemas für Observation, Classification, Effect, Verification und Closure;
- risikobasierte Evidence-Profile R0–R3 sowie die v2-Kreuzproduktmatrix mit kanonischer Zielkritikalität;
- deterministische Übergangsregeln;
- Konformitätsfixtures und eine zustandslose Referenzauswertung.

Er besitzt ausdrücklich nicht:

- Aufgaben, Abhängigkeiten oder Claims — **Bureau**;
- Ausführung, Leases, Audit oder Recovery — **Grabowski**;
- Systemzwecke und Wahrheitsgrenzen — **Systemkatalog**;
- Fleet-Mitgliedschaft — **Metarepo**;
- Ereignisgeschichte — **Chronik**;
- Deployment- und Runtime-Wahrheit — jeweiliger Dienst;
- Projektionen — **Leitstand** und **Schauwerk**.

## Regelkreis

```text
Observation → Classification → Required Evidence
            → Effect Receipt → Verification Receipt → Closure Receipt
```

Die Referenzauswertung liefert genau einen Status:

- `transition_allowed`
- `evidence_missing`
- `conflicting_evidence`
- `source_stale`
- `blocked`
- `terminally_closed`

## Installation und Nutzung

```bash
python -m venv .venv
.venv/bin/pip install -e .
regelkreis evaluate conformance/valid/r2-terminal.json
```

Die Ausgabe ist deterministisch: gleiche Eingaben und gleiche Vertragsdateien erzeugen bytegleiche JSON-Ausgaben. Es gibt keine Netzwerkzugriffe, Datenbank, Uhrzeitabfrage oder Mutation.

## Evidence-Profile

v1 bewertet Änderungsrisiken R0–R3 unverändert:

| Profil | Typischer Fall | Mindestanforderung |
|---|---|---|
| R0 | generierte Dokumentation | deterministische Regeneration |
| R1 | interne Codeänderung | Tests, Review, Mergebeleg |
| R2 | Dienst- oder Runtimeänderung | R1 plus Deployment und Live-Verifikation |
| R3 | Security, Daten, irreversible Wirkung | R2 plus unabhängige Prüfung und Recovery-Beleg |

v2 ergänzt die unabhängige kanonischer Zielkritikalität. Die 4×5-Matrix fordert Recovery-, Degradations-, Cleanup- und Return-to-Primary-Belege nur für die dafür definierten Kreuzprodukte. Details und Negativkontrollen stehen unter [`docs/resilience-evidence-profiles-v2.md`](docs/resilience-evidence-profiles-v2.md).

## Entwicklung

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
python -m regelkreis.cli validate-contracts
```

Architektur, Autoritätsgrenzen, Threat Model sowie verbindliche SemVer- und Migrationsregeln stehen unter [`docs/`](docs/).

## Status

Version `1.1.0` ergänzt additive v2-Dokumente für resilienzbewusste Evidence-Profile. v1 bleibt vollständig lesbar und bytegleich auswertbar. Die Referenzfixture `R2-foundational` belegt Recovery, begrenzten Degradationsbetrieb, Cleanup, Rückkehr zum Primärpfad, unabhängige Failure-Domains und Split-Brain-Negativkontrolle.
