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
- ungültig codierte oder auf nicht-reguläre Dateiziele gerichtete JSON-Eingaben;
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
- JSON-Dateien sind auf 4 MiB und höchstens 64 verschachtelte Container-Ebenen begrenzt; Parser-Rekursion wird als ungültige Eingabe fail-closed behandelt;
- der Dateilader öffnet JSON-Pfade einmalig nichtblockierend, prüft Typ und Größe per `fstat()` auf demselben Deskriptor und liest höchstens 4 MiB + 1 Byte; Verzeichnisse/FIFOs und andere nicht-reguläre Ziele, ungültiges UTF-8 sowie Dateisystem-/Zugriffsfehler werden in den normalen `ContractValidationError`-/`invalid_input`-Pfad überführt;
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
