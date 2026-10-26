# Forschungsrichtung nach der Besprechung mit Andreas

Stand: 26.10.2026. Diese fachliche Zusammenfassung ersetzt die zwischenzeitlichen
Chat-Vorschläge zur sofortigen großen Nutzen-/Verifikationsstudie. Das vollständige
Transkript bleibt im privaten Übergabearchiv. Die Transkription enthält ASR-Fehler
und keine verlässlichen Sprecherlabels; sie ist keine autorisierte wörtliche Mitschrift.
Eingang in der damaligen Session: 13.10.2026; tatsächliches Gesprächsdatum unbestätigt.

## Verbindliche Arbeitsrichtung

Der Nutzer hat entschieden, wieder im ursprünglichen WCWV-Repository zu arbeiten.
POS war eine technisch nützliche Seitenentwicklung, hat aber den unmittelbaren
Arbeitsumfang zu früh auf einen größeren P-/D-Pilot und Zusatzbedingungen erweitert.
Die nächsten Ergebnisse sollen Claim-Beispiele und eine begründete Zielreferenz sein.

Das Gespräch legt folgende Reihenfolge nahe:

1. Begründen, weshalb explizite Sicherheitsclaims eine sinnvolle Darstellung sind.
2. An verschiedenen Codebeispielen erwartete Claims selbst ausarbeiten.
3. Korrektheit und Sinnhaftigkeit dieser Zielreferenz fachlich kontrollieren lassen.
4. Generierte Claims aus Report oder Code mit der Referenz vergleichen.
5. Granularität, unterschiedliche Abstraktionsebenen und mögliche Verknüpfungen untersuchen.

Eine vollständige Prüfungspipeline wäre eine spätere Erweiterung. Die Anzahl
künftiger Papers, eine Hauptstichprobe mit 200 Fällen und konkrete Reviewerzusagen
sind nicht abschließend beschlossen. Aktuell planen wir ein klar begrenztes erstes
Vorhaben; eine zweite Veröffentlichung ist kein Arbeitsauftrag.

## Begründung der Claim-Darstellung

Zu untersuchende Argumente sind einzeln adressierbare Aussagen, nachvollziehbare
Quellen, dokumentierte Voraussetzungen, Vergleichbarkeit über Antworten und
Revisionen sowie die Vorbereitung gezielter späterer Prüfungen. Das sind zunächst
Motivationen, keine empirisch nachgewiesenen Verbesserungen.

Für jedes Argument sollen ein konkreter Arbeitsablauf, ein Beispiel und passende
Literaturbelege ergänzt werden. Verwandte Arbeiten und ihre begrenzte Übertragbarkeit
sind in der archivierten POS-Dokumentation eingeordnet. Insbesondere behandeln
DecompScore und VeriScore Zerlegung und Kontext; LLMSAN/GPTAid liefern verwandte
Security-Prüfideen. CAE/SACM motivieren die Trennung von Aussage, Kontext und Evidenz.
Keine dieser Nennungen belegt automatisch Neuheit oder den Nutzen unseres Profils.

Andreas verwies außerdem auf Tam et al. (2024), *Let Me Speak Freely?*:
https://aclanthology.org/2024.emnlp-industry.91/ . Die Arbeit betrachtet den Einfluss
von Formatvorgaben auf die Aufgabenleistung und auch natürliche Sprache mit
anschließender Formatumwandlung. Ein bloßes „Fließtext gegen JSON“ ist daher keine
ausreichende Abgrenzung. Ob neuere Modelle die fachlichen Probleme lösen, wurde
nicht gezeigt. Security-spezifische Neuheit bleibt durch Literaturarbeit abzusichern.

## Zielreferenz ist nicht dasselbe wie ein Vergleichsverfahren

Mit der im Gespräch genannten manuellen „Baseline“ sind erwartete Zielclaims
gemeint. Das ist eine Referenz, gegen die Erzeugungsverfahren bewertet werden.
Die Satzaufteilung und die VeriScore-basierte Extraktion aus POS sind dagegen
Vergleichsverfahren; sie sind keine Wahrheitsreferenzen.

Zwei Referenzen bleiben nötig, wenn beide Erzeugungswege betrachtet werden:

- **Codereferenz:** Welche Aussagen und konkreten offenen Fragen erlaubt das
  identische bereitgestellte Codepaket? Je Einheit Bedingungen, Scope und Fundstellen.
- **Reportreferenz:** Was behauptet der konkrete Report, auch falls es fachlich
  falsch ist? Originalzitate erhalten und den Report nicht mit Codewissen reparieren.

So bleibt unterscheidbar, ob Inhalte schon im Report fehlen oder erst bei seiner
Zerlegung verloren gehen. Der P-Extraktor darf keine zusätzliche Codeanalyse erhalten.
Fix, PoV, Advisory, Datasetlabels und Zielreferenzen bleiben aus Modellkontexten heraus.

## Prüfbarkeit und Abstraktion

Zunächst anhand von Beispielen klären: Welche Aussage kann eigenständig beurteilt
werden? Welche Bedingungen müssen im Satz bleiben? Wann beschreiben mehrere Claims
denselben Inhalt auf anderer Ebene? Atomar bedeutet nicht maximal kurz.

Eine konkrete Operation, ein zusammengefasster Datenfluss und eine mögliche
Angriffswirkung sind unterschiedliche Ebenen. Die Wirkung benötigt gegebenenfalls
zusätzliche Annahmen über Aufrufer, Rechte und Umgebung. Links zwischen Aussagen
sind weder Beweise noch ein Ersatz für erhaltene Bedingungen.

Hierarchien sind eine zu erprobende Idee, kein beschlossenes Datenmodell. Das
POS-Feld context_claim_ids stellt Verständnisbezüge dar, keine Abstraktions- oder
Beweiskanten. Erst eine kleine manuelle Tabelle erproben; keine Graphplattform bauen.

Ein zusätzliches Ranking „wichtig/unwichtig“ ist vorerst nicht erforderlich.
Trotzdem muss der Zweck der Zielreferenz begrenzt werden, damit triviale Operationen
und Duplikate nicht künstlich die Abdeckung erhöhen.

## Vergleich und Rolle menschlicher Unterstützung

Zwei Fragen auseinanderhalten:

1. Sind die selbst erstellten Zielclaims fachlich korrekt und sinnvoll gewählt?
2. Treffen die Modelloutputs diese Inhalte einschließlich Bedingungen und Grenzen?

Menschen sollen insbesondere die erste Frage kontrollieren. Für die zweite kann
Unterstützung durch Software oder Modelle geprüft werden; zuverlässiges automatisches
semantisches Matching ist noch nicht implementiert oder validiert. Ein anderer
Wortlaut, eine Aufteilung in mehrere Claims oder eine andere zulässige Abstraktion
darf nicht allein als Fehler gelten. Zusatzclaims außerhalb der Referenz separat
beurteilen; sie können richtig sein und eine Lücke in der Referenz zeigen.

Für neue Evaluationsfälle die Referenz vor Einsicht in Outputs fixieren. Bereits
bekannte Fälle, KI-assistierte Entwürfe und Vorwissen explizit dokumentieren. Alte
Modellantworten bleiben unverändert; Änderungen nach Einsicht in Ergebnisse brauchen
eine neue, begründete Versuchsfassung. Keine Auswahl des besten Wiederholungslaufs.

## Vorschläge, die vorerst zurückgestellt sind

- Eine zentrale Forschungsfrage zum allgemeinen Nutzen von Claims durch eine
  komplette Prüfung mit versus ohne Claim-Zwischenschritt.
- Menschliche Nutzerstudie, LLM-as-a-Judge als alleinige Wahrheitsinstanz und
  automatische Erzeugung von CodeQL-Abfragen.
- CodeQL-/SMT-/OpenJML-Integration, Agentenplattform oder universeller Verifier.
- Neue große Modellläufe, eine feste Hauptstudien-Fallzahl oder eine neue Kostenzusage.

Falls später Werkzeugprüfung untersucht wird, brauchen Report und natürlichsprachliche
Claims jeweils eine Übersetzung in ausführbare Prüfungen. Formatgültigkeit einer
Abfrage beweist weder korrekte Übersetzung noch die ganze Angriffsaussage.

## Nächste Vorlage für Andreas

Eine kurze Begründung und drei konkrete Entwicklungsbeispiele vorlegen. Je Beispiel:
Codeausschnitt mit Herkunft, Zielclaims, Bedingungen, offene Fragen, akzeptable
alternative Zerlegung und gegebenenfalls höhere Aussage mit zusätzlich benötigten
Belegen. Daneben vorhandene Modelloutputs einordnen. Das Ergebnis ausdrücklich als
Arbeitsentwurf kennzeichnen und fachliches Gegenlesen organisieren.
