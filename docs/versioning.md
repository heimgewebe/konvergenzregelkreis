# Versionierung und Migration

## SemVer

Das Paket und der Protokollsatz folgen Semantic Versioning. Python-Paketversion, `regelkreis.__version__`, Git-Tag und GitHub-Release müssen identisch sein.

- **Patch**: Fehlerkorrekturen ohne Änderung akzeptierter oder erzeugter Vertragsformen.
- **Minor**: additive optionale Felder, neue optionale Receipt-Kinds oder neue Fixtures; bestehende v1-Dokumente bleiben gültig und bytegleich auswertbar.
- **Major**: neue Pflichtfelder, entfernte oder umgedeutete Werte, geänderte Statuspräzedenz, geänderte Exit-Codes oder andere inkompatible Semantik.

## Dokumentversionen

`schema_version` versioniert jeden Dokumenttyp unabhängig von der Paketversion. Inkompatible Verträge erhalten neue Schemadateien und IDs; bestehende v1-Dateien werden nicht still umgedeutet. Evidence-Profile bleiben über ihren SHA-256 bindbar.

## Migrationsregeln

1. Der Regelkreis migriert Consumerdaten nie in-place.
2. Eine Migration ist eine explizite Transformation mit Quell- und Zielversion, deterministischen Fixtures und eigenem Review.
3. Alte Major-Verträge bleiben mindestens bis zum nächsten Major-Release lesbar oder erhalten einen dokumentierten externen Migrationspfad.
4. Unbekannte Pflichtsemantik und widersprüchliche Receipts bleiben fail-closed.
5. Exit-Codes und Statuspräzedenz sind innerhalb 1.x stabil.
6. Release-PRs prüfen Paketversion, Modulversion, Konformitätsfixtures und Wheel-Isolation gemeinsam.
