# Threat Model

## Schutzgüter

- korrekte Zuordnung von Belegarten;
- fail-closed Verhalten bei Konflikten und fehlenden Belegen;
- reproduzierbare Ergebnisse;
- klare Trennung externer Autoritäten;
- keine unbeabsichtigte Offenlegung privater Betriebsdaten.

## Angreifbare Eingaben

Assessment-Dateien, Profile und Schemas gelten als nicht vertrauenswürdig. Relevante Angriffe:

- extrem große oder tief verschachtelte JSON-Eingaben;
- absichtlich widersprüchliche Receipts;
- formal gültige, aber sachlich falsche Evidence-Referenzen;
- Schema- oder Profilmanipulation;
- Pfadangriffe über frei gewählte Contract-Roots;
- öffentliche Fixtures mit Secrets oder privaten Infrastrukturdetails.

## Gegenmaßnahmen v0.1

- strikte JSON-Schemas mit `additionalProperties: false`;
- Hashbindung für Quellen und Receipts;
- deterministische Konflikterkennung;
- keine Netzwerk-, Datenbank- oder Mutationsfunktionen;
- keine automatische Dereferenzierung von Evidence-Referenzen;
- versionierte Profile und Profilhash in jedem Ergebnis;
- CI prüft Schemas, Profile, Fixtures und deterministische Ausgabe.

## Bewusste Grenzen

Die Referenzauswertung beweist nicht:

- dass ein externer Evidence-Erzeuger autorisiert war;
- dass eine referenzierte Quelle existiert;
- dass ein SHA-256-Inhalt semantisch korrekt ist;
- dass ein System nicht kompromittiert wurde;
- dass ein erfolgreicher technischer Smoke-Test Produktnutzen erzeugt.

Diese Aussagen benötigen separate Primärquellen und gegebenenfalls eigene Verification Receipts.
