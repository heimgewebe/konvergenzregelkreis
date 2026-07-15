# Protokoll

Die JSON-Schemas in diesem Verzeichnis sind die kanonische öffentliche Vertragsquelle.

## Dokumente

- `assessment-request.v1.schema.json` — vollständiges Eingabepaket;
- `observation.v1.schema.json` — hashgebundene Primärquellenbeobachtung;
- `classification.v1.schema.json` — Änderungsklasse, Semantik und Blocker;
- `effect-receipt.v1.schema.json` — Beleg einer Mutation;
- `verification-receipt.v1.schema.json` — Beleg einer Wirkungsprüfung;
- `closure-receipt.v1.schema.json` — Task-, Chronik-, Cleanup- und Restrisikobindung;
- `evidence-profile.v1.schema.json` — Anforderungen eines Risikoprofils;
- `transition-assessment.v1.schema.json` — deterministisches Auswertungsergebnis.

## Versionsregel

Additive optionale Felder dürfen innerhalb einer Version nicht eingeführt werden, solange `additionalProperties: false` gilt. Jede Strukturänderung erfordert daher eine neue Schema-Version oder eine explizit dokumentierte Revision mit vollständiger Consumerprüfung.

Schemas und Profile werden unverändert in das Wheel eingebettet. Das Ergebnis enthält den SHA-256 des tatsächlich verwendeten Profils.
