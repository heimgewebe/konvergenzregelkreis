# Changelog

Alle wesentlichen Änderungen werden hier dokumentiert.

## [Unreleased]

## [1.1.2] - 2026-07-21

### Changed

- Resilienzprofil-Index greift nach erfolgreicher Schema-Validierung direkt auf Pflichtfelder zu, statt fehlende Werte als `"None"` zu verschleiern;
- Evidence-Helfer akzeptieren Sequenzen direkt und vermeiden unnötige Kopien validierter Receipt-Arrays;
- Missing-Evidence wird direkt als Menge aufgebaut;
- Schema-Versionen normalisieren explizit Integer und ganzzahlige Floats, während Bool- und gebrochene Werte fail-closed bleiben;
- Statuspräzedenz und der bewusste Verzicht auf einen root-basierten Profilcache sind dokumentiert.

### Tests

- Abdeckung für leere v1-Profile, fehlende Pflichtfelder in v2-Profilzellen, `unknown` plus Split-Brain sowie ungültige Bool-/Fractional-Schema-Versionen ergänzt.

## [1.1.1] - 2026-07-20

### Changed

- Versionsdispatch und Request-Untervalidierung für v1/v2 datengesteuert zentralisiert;
- gemeinsame Evidence- und Statusauswertung reduziert Duplikation zwischen v1 und v2, ohne Statuspräzedenz oder Ausgaben zu ändern;
- Resilienzprofil-Zellen werden über einen validierten Index gewählt und Duplikate nennen jetzt die konkrete Zelle;
- explizite Diagnose für leere Profildateien ergänzt;
- Paket- und Modulversion auf 1.1.1 synchronisiert.

### Tests

- Robustheitsabdeckung für degradierte Modi, Common-Mode, Return-to-Primary, Konflikt-vor-Stale-Präzedenz, Schema-Grenzen und bedingte Split-Brain-Nachweise erweitert.

## [1.1.0] - 2026-07-20

### Added

- additive v2-Protokollgeneration mit getrennten Achsen für Änderungsrisiko R0–R3 und den kanonischen Systemkatalog-Zielkritikalitäten;
- vollständige, hashgebundene 4×5-Resilienz-Profilmatrix mit den kanonischen Systemkatalog-Kritikalitäten;
- Recovery-, begrenzte Degradations-, Cleanup-, Return-to-Primary-, Common-Mode- und Split-Brain-Nachweise;
- fail-closed Negativkontrollen für fehlende Recovery, veraltete Kritikalität, Common-Mode-Widersprüche und fehlende Split-Brain-Prüfung.

### Changed

- Paket- und Modulversion auf 1.1.0 synchronisiert;
- Referenzauswertung dispatcht deterministisch zwischen unveränderter v1- und neuer v2-Semantik.

## [1.0.0] - 2026-07-16

### Added

- zweiter unabhängiger R2-Live-Pilot für Grabowski PR #235 von Merge über unveränderliches Deployment bis Laufzeit- und Liveprobe;
- öffentliche fail-closed Konfliktfixture mit bewusst divergierenden Deployment-Identitäten;
- verbindliche SemVer-, Dokumentversions- und Migrationsregeln für 1.x.

### Changed

- Paket- und Modulversion auf 1.0.0 synchronisiert;
- Reifestatus auf Production/Stable gesetzt;
- Masterplan T008 und T011 abgeschlossen.

## [0.2.0] - 2026-07-16

### Added

- terminal geschlossene öffentliche R2-Fixture für den Systemkatalog-Drift-Pilot;
- dokumentierte Belegkette über Merge, Null-Drift, Leitstand, Schauwerk, Bureau, Chronik und Worktree-Archivierung.

### Changed

- Masterplan und Status auf den nachgewiesenen Integrationsstand fortgeschrieben.


## [0.1.0] - 2026-07-15

### Added

- öffentliches Repository `heimgewebe/konvergenzregelkreis`;
- strikte JSON-Schemas für Observation, Classification, Effect, Verification, Closure und Transition Assessment;
- risikobasierte Evidence-Profile R0–R3;
- zustandslose, deterministische CLI `regelkreis`;
- fail-closed Konflikt-, Quellenfrische-, Blocker- und Missing-Evidence-Auswertung;
- Konformitätsfixtures und Regressionstests;
- installierbares Wheel mit eingebetteten Vertragsdateien;
- commitgepinnte GitHub-Actions-CI;
- Autoritätsgrenzen, Architektur, Threat Model und Integrationsleitfaden.
