# Architektur

## Ziel

Der Konvergenzregelkreis prüft, ob eine Änderung die für ihre Risikoklasse erforderlichen Belege besitzt. Er erzeugt keine Belege selbst und verändert keine externen Systeme.

## Datenfluss

```text
Primärquellen
  → Observation
  → Classification
  → Evidence Profile R0–R3
  → Effect Receipts
  → Verification Receipts
  → Closure Receipt
  → Transition Assessment
```

## Trennung der Belege

- **Observation** bindet Behauptungen an beobachtete Primärquellen.
- **Classification** ordnet Art, Semantik und Blocker ein.
- **Effect Receipt** belegt eine Mutation, etwa Merge oder Deployment.
- **Verification Receipt** belegt eine Prüfung der Wirkung.
- **Closure Receipt** bindet Aufgabenabschluss, Ereignisgeschichte, Restgefahren und Cleanup.

Ein Effect Receipt darf niemals als Verification Receipt interpretiert werden.

## Determinismus

Die Referenzauswertung verwendet ausschließlich:

- die übergebene Assessment-Datei;
- versionierte JSON-Schemas;
- das ausgewählte versionierte Evidence-Profil.

Sie liest keine Uhr, Umgebung, Git-Remote, Datenbank oder Netzwerkquelle. Quellenfrische ist deshalb ein explizites Feld der Observation und keine lokale Zeitschätzung.

## Statuspriorität

1. widersprüchliche Belege;
2. veraltete oder unbekannte Quelle;
3. explizite Blocker oder fehlgeschlagene Verifikation;
4. fehlende Belege;
5. zulässiger Übergang;
6. terminaler Abschluss.

Diese Reihenfolge verhindert, dass ein formal vollständiges Paket einen Quellen- oder Evidenzkonflikt überdeckt.
