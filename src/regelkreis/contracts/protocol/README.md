# Protokoll

Die JSON-Schemas in diesem Verzeichnis sind die kanonische öffentliche Vertragsquelle.

## Dokumente

### Generation v1

- `assessment-request.v1.schema.json` — vollständiges Eingabepaket;
- `observation.v1.schema.json` — hashgebundene Primärquellenbeobachtung;
- `classification.v1.schema.json` — Änderungsklasse, Semantik und Blocker;
- `effect-receipt.v1.schema.json` — Beleg einer Mutation;
- `verification-receipt.v1.schema.json` — Beleg einer Wirkungsprüfung;
- `closure-receipt.v1.schema.json` — Task-, Chronik-, Cleanup- und Restrisikobindung;
- `evidence-profile.v1.schema.json` — Anforderungen eines Risikoprofils;
- `transition-assessment.v1.schema.json` — deterministisches Auswertungsergebnis.

### Resilienz-Erweiterung v2

- `assessment-request.v2.schema.json` — v2-Eingabepaket mit v2-Klassifikation und v2-Verifikationen;
- `classification.v2.schema.json` — getrennte Achsen `change_risk` und `target_criticality`, Quellenfrische und Failure-Domains;
- `verification-receipt.v2.schema.json` — zusätzliche Nachweisarten für Recovery, begrenzten Degradationsbetrieb, Cleanup, Rückkehr zum Primärpfad, Common-Mode und Split-Brain-Negativkontrolle;
- `closure-receipt.v2.schema.json` — explizite Recovery-, Degradations- und Return-to-Primary-Belege;
- `evidence-profile.v2.schema.json` — vollständige 4×5-Profilmatrix;
- `transition-assessment.v2.schema.json` — v2-Ergebnis mit ausgewählter Matrixzelle und Profilhash.

`observation.v1` und `effect-receipt.v1` werden in v2 bewusst wiederverwendet, weil ihre Semantik unverändert bleibt. Bestehende v1-Dokumente und v1-Ausgaben werden nicht umgedeutet.

## Versionsregel

Additive optionale Felder dürfen innerhalb einer Version nicht eingeführt werden, solange `additionalProperties: false` gilt. Jede Strukturänderung erfordert daher eine neue Schema-Version oder eine explizit dokumentierte Revision mit vollständiger Consumerprüfung.

Schemas und Profile werden unverändert in das Wheel eingebettet. Das Ergebnis enthält den SHA-256 des tatsächlich verwendeten Profils.
