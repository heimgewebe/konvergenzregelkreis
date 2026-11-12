# Operator-Consumer-Abdeckung

Stand: 2026-07-26

## Zweck

Dieses Dokument beschreibt die öffentlich belegbare Integration des zustandslosen Konvergenzprotokolls in einen Operator-Consumer. Es ist keine Laufzeitwahrheit und ersetzt weder den aktuellen Consumer-Code noch eine konkrete, vom Evaluator erzeugte Transition-Assessment-Ausgabe.

## Bekannter Consumer

`heimgewebe/grabowski` stellt den read-only Operator-Grip `convergence-assess` bereit. Der Consumer erwartet einen bereits erzeugten Assessment-Request und bindet vor der Auswertung:

- den bytegenauen SHA-256 des Requests;
- den erwarteten Git-Commit des Protokollrepositories;
- einen sauberen Protokollcheckout;
- die Identität des ausführbaren Evaluators;
- die Konsistenz von Assessment-Status und Exit-Code;
- einen erneuten Protokoll- und Evaluator-Readback nach der Auswertung.

Nur eine Transition-Assessment-Ausgabe mit `status=terminally_closed` ergibt eine positive Abschlussentscheidung. Fehlende, veraltete, blockierte oder widersprüchliche Evidenz bleibt fail-closed.

## V2-Abschlussautorität für direkte Nutzeraufträge

Die bestehende v2-Resilienzmatrix verlangt eine verantwortliche Arbeitsquelle
(`bureau_task_ref`). Ein autorisierter direkter Grabowski-Auftrag ist aber
bereits als create-only `operator-obligation` belegt und muss dafür **keinen**
künstlichen Bureau-Task erzeugen. V2 akzeptiert alternativ:

- `closure.operator_obligation_ref` in der Form
  `grabowski:operator-obligation:<id>@sha256:<open-record-sha256>`;
- exakt dazu passende `observation.source_refs` mit
  `kind=operator_obligation`, demselben `ref` und dem SHA-256 der
  unveränderlichen Grabowski-`open.json`.

Beide Quellen zusammen sind widersprüchlich (`conflicting_evidence`);
eine ungebundene direkte Quelle bleibt `evidence_missing`. V1 und
bestehende reine Bureau-Abschlüsse bleiben unverändert. Die statische
Matrixpflicht `bureau_task_ref` ist in V2 nur für den **tatsächlich als
Bureau-Task geführten** Arbeitsursprung wörtlich zu lesen.

Die zustandslose Referenzauswertung **prüft nicht**, ob die genannte
Grabowski-Datei existiert oder ob eine konkrete Nutzerfunktion erfolgreich
war. Der Grabowski-Consumer muss vor jeder systemischen `completed`-Mutation
den exakten Obligation-ID-/Open-Record-Hash gegen seine Primärquelle und
den bereits gebundenen Request live verifizieren. Protokoll-PASS ist
niemals Ersatz für Task-, Merge-, Deployment- oder Nutzer-Readback.
## Abdeckungsmatrix

| Abschlussaspekt | Protokoll | Bekannter Consumer | Verbleibende Autorität |
|---|---|---|---|
| Assessment-Schema und Evidence-Profile | definiert und validiert | lädt den gepinnten Evaluator | Konvergenzregelkreis |
| Request-Integrität | bewertet den Inhalt | bindet die Requestbytes per SHA-256 | Consumer |
| Protokollidentität | versionierte Vertragsdateien | bindet exakten Git-Commit und sauberen Checkout | Consumer |
| Deterministische Auswertung | bytegleiche Ausgabe bei gleichen Eingaben | prüft Status-/Exit-Code-Konsistenz | Konvergenzregelkreis und Consumer |
| Abschlussentscheidung | liefert ein Transition Assessment mit `status=terminally_closed` oder einem Blocker | übersetzt ausschließlich `status=terminally_closed` in `allow_closure` | Consumer |
| Taskstatus und Claims | nicht zuständig | keine Mutation | Bureau |
| Merge-Autorisierung | nicht zuständig | keine Mutation | jeweiliger Merge-Governor |
| Deployment- und Runtime-Wahrheit | bewertet nur vorgelegte Receipts | liest sie nicht automatisch aus den Primärquellen | jeweiliger Dienst und Consumer |
| Chronikpersistenz | nicht zuständig | wird durch das Assessment nicht hergestellt | Chronik |
| Checkout-Cleanup | bewertet vorgelegte Cleanup-Evidenz | führt durch das Assessment kein Cleanup aus | Grabowski |

## Nicht belegte universelle Durchsetzung

Die Existenz eines korrekten Consumers beweist nicht, dass jeder mögliche Abschlussweg ihn zwingend aufruft. Ein Operatorpfad kann das Protokoll umgehen, wenn er:

1. einen Abschluss mutiert, ohne vorher einen hashgebundenen Assessment-Request auszuwerten;
2. die erzeugte Transition-Assessment-Ausgabe und das sie bindende Consumer-Receipt nicht an die konkrete Abschlussmutation bindet;
3. einen älteren oder abweichenden Protokollcommit verwendet;
4. lediglich Merge-, Deployment- oder Taskstatus als Wirkungskontrolle behandelt;
5. einen nichtterminalen Transition-Assessment-Status ignoriert.

Diese Risiken müssen im jeweiligen Consumer durch ein technisches Gate verhindert werden. Das Protokollrepository kann seine eigene Verwendung absichtlich nicht erzwingen, weil es keine Control Plane und keine Mutationsautorität besitzt.

## Abnahmekriterium für Consumer

Ein Consumer gilt erst dann als durchgängig integriert, wenn alle für seinen Scope relevanten Abschlussmutationen fail-closed ein unverändertes Consumer-Receipt verlangen, das eine request-, protokoll- und mutationsgebundene Transition-Assessment-Ausgabe mit `status=terminally_closed` belegt und Negativtests das Umgehen dieses Gates verhindern.
