# Claim-Codebook

Arbeitsregeln für manuelle und automatische Zerlegung. Wir erfassen Behauptungen
im Finding; ihre Wahrheit wird hier nicht geprüft. Die Kategorien sind vorläufig.

## Ziel und Ablauf

Wir erfassen, **was ein Finding behauptet**, einschließlich möglicher Fehler.
Eine originalgetreue Extraktion kann eine falsche Behauptung enthalten.
Code, Fix und PoV dienen später der Wahrheitsprüfung; sie dürfen den Report bei
der Zerlegung weder korrigieren noch um zusätzliche Aussagen ergänzen.

1. Titel und vollständigen Report lesen. Satzgrenzen sind nur Lesehilfen.
2. Pro unabhängig beurteilbarer Behauptung einen Claim-Block im
   [Arbeitsblatt](manual_annotation_template.md) ausfüllen.
3. Originalzitat und bedeutungstreue Proposition festhalten, danach typisieren.
4. Titel und jeden Satz mit den Claims abgleichen; Auslassungen begründen.
5. Aussagen und Kategorien inhaltlich prüfen; Grenzfälle festhalten.

Für diesen Durchgang reichen Markdown und der gespeicherte Report. Keine feste
Claim-Anzahl und keine Pflicht, jede Familie zu verwenden. Menschliche Bearbeitung
mit Namen/Kürzel und Datum festhalten. Bereits vorhandenes Wissen über Code/Fix/PoV
angeben; dieser Entwicklungspilot ist keine verblindete oder unabhängige Evaluation.

## Zerlegungsregeln

- **Eine Proposition je Claim:** Gegenstand und Aussage vollständig benennen.
  Trennen, wenn Aussagen getrennt beurteilt werden können und ihr Zusammenhang erhalten bleibt. Ein Satz kann mehrere Claims
  enthalten, auch mit unterschiedlichen Familien. Zuerst die Propositionen zerlegen,
  danach jede einzeln typisieren. Dasselbe Zitat darf mehrere unterschiedliche
  Propositionen belegen. Keine Duplikate nur zum Wechseln der Familie; einzelne
  Wörter oder jede Codeposition sind nicht automatisch Claims.
- **Beleg im Finding:** Exakte Zitate aus `title` oder `report` übernehmen, mit
  Satzkennung. Für aufgelöste Verweise wie „this value“ auch den nötigen vorherigen
  Text zitieren. Mehrere Zitate sind erlaubt; Kürzungen nicht als Original ausgeben.
  Bei mehrfach vorkommendem Text die Fundstelle zusätzlich beschreiben.
- **Bedeutung erhalten:** Akteur, Negation, „only“, Quantoren, „could/potentially“,
  Bedingungen und Geltungsbereich bleiben in der Proposition. Eine Bedingung nicht
  in einen zusätzlichen Claim verwandeln, der ihre tatsächliche Erfüllung behauptet.
- **Beziehungen erhalten:** Ursache/Wirkung, Alternativen und Bedingungen nicht
  durch Aufteilung verstärken. Aus „A oder B könnte eintreten“ nicht die zwei
  unbedingten Zusagen „A tritt ein“ und „B tritt ein“ machen. Wenn sich die Relation
  beim Trennen nicht treu darstellen lässt, gemeinsam lassen und Grenzfall notieren.
- **Kontext erhalten:** Verweise nur aus dem Finding auflösen. Benötigte andere
  Claims über ihre IDs nennen; ungelöste Mehrdeutigkeit stehenlassen. Kontextverweise
  sind keine nachgewiesenen Datenflüsse oder logischen Beweise.
- **Nicht verbessern:** Behauptete Methoden, Pfade, Zeilen und Payloads unverändert
  zuordnen, auch wenn sie vermutlich falsch sind. Keine Anmeldung, Filter oder
  Auswirkungen aus dem Schwachstellenlabel ergänzen. Fehlende Angaben als
  „nicht genannt“ markieren; eine mehrdeutige Angabe als „unklar“.
- **Vollständigkeit:** Titel mitprüfen. Fasst er den Report nur zusammen oder
  wiederholt bereits erfasste Aussagen, keinen zusätzlichen Claim anlegen. Zusätzliche
  Behauptungen separat erfassen. Empfehlungen oder nicht zuordenbare Inhalte im
  Abdeckungscheck ausdrücklich behandeln, nicht still weglassen.

## Vorläufige Familien

Eine Hauptfamilie nach dem Kern der Aussage wählen und kurz begründen. Bei
Überschneidungen zuerst eine sinnvolle Trennung prüfen; bei echter Mehrdeutigkeit
`unclear` verwenden und die möglichen Zuordnungen notieren.

| Familie | Leitfrage / Abgrenzung | Synthetisches Beispiel |
|---|---|---|
| `location` | Welche Operation oder welches Symbol befindet sich wo? Ein Pfad im Claim allein macht ihn nicht zum Location-Claim. | „In `Handler.handle()` wird `execute()` aufgerufen.“ |
| `data_flow` | Woher stammt ein Wert, wer kontrolliert ihn, wohin gelangt er? | „Der Requestparameter wird als Argument an `execute()` übergeben.“ |
| `protection_precondition` | Welcher Schutz besteht/fehlt, oder welche Bedingung gilt für den beschriebenen Pfad? | „Vor dem Aufruf wird der Parameter nicht validiert.“ |
| `exploitability_impact` | Ist ein konkreter Angriff möglich, oder welche Wirkung könnte er haben? Als Untertyp `exploitability`, `impact` oder begründet `unclear` angeben. Getrennte Aussagen trennen. | „Ein Angreifer könnte mit Payload P diesen Pfad auslösen.“ / „Dadurch könnten fremde Datensätze gelesen werden.“ |
| `other` | Aussage verständlich, aber keine Familie passt. | „Der Patch sollte eingespielt werden.“ |
| `unclear` | Zuordnung wegen Mehrdeutigkeit oder unzureichendem Kontext offen. | „Das ist unsicher“, ohne erkennbaren Bezug. |

Reines Parser-/Transformationsverhalten ohne explizite Schutz- oder
Datenflussbehauptung vorläufig als other behandeln. Ein eigenständiges Titellabel
ist ebenfalls other, soweit es mehr als eine Zusammenfassung des Reports enthält.
Ein Pfad oder Parametername allein entscheidet nicht über die Familie.
Diese Beispiele sind erfunden und keine Annotation des aktuell zerlegten Findings.

## Beispiel: mehrere Claims aus einem Satz

Synthetischer Report: „In Handler.run wird request.name ohne Validierung
an lookup übergeben.“

- „In Handler.run wird lookup aufgerufen.“ → location.
- „request.name wird an lookup übergeben.“ → data_flow.
- „request.name wird ohne Validierung an lookup übergeben.“ → protection_precondition.

Alle drei Claims dürfen denselben Satz zitieren. Sie unterscheiden sich in der
zu prüfenden Behauptung; nötiger Gegenstand und Kontext dürfen sich wiederholen.
Eine bloße Zeilenangabe bleibt kein eigener Claim. Dies ist ein synthetisches
Beispiel, keine Zielanzahl oder Vorlage für die Anzahl der Claims eines Findings.

## Beispiel für den Erhalt von Bedingungen

Synthetischer Report: „Die Route erfordert keine Anmeldung. Über diese Route könnte ein Angreifer
Dateien außerhalb des Upload-Verzeichnisses lesen, sofern der Dienstprozess dafür
Leserechte besitzt.“

- C01: „Die Route erfordert keine Anmeldung.“ → `protection_precondition`;
  Negation erhalten, als Tatsache formuliert.
- C02: „Über diese Route könnte ein Angreifer Dateien außerhalb des
  Upload-Verzeichnisses lesen, sofern der Dienstprozess dafür Leserechte besitzt.“
  → `exploitability_impact` / `impact`; beide Sätze als Quellen, C01 als Kontext.
  „Könnte“ und Rechtebedingung bleiben erhalten; der Report behauptet nicht, dass
  diese Rechte tatsächlich vorliegen. Keine Aussage über beliebige Dateien ableiten.

## Menschliches Review und Abschluss

Sind alle Aussagen abgedeckt, sinnvoll getrennt und originalgetreu,
einschließlich Unsicherheit und Bedingungen? Passt die Familie, und ist ihre
Begründung nachvollziehbar? Dafür sind keine zusätzlichen Prüffelder oder
Änderungsprotokolle pro Claim erforderlich.
Die Wahrheit bleibt für sämtliche Claims `not_evaluated`; „Extraktion geprüft“
bedeutet nicht „Schwachstelle bewiesen“.

Änderungen direkt in dieser Datei pflegen; die Historie liegt in Git.
Für neue Modellläufe speichert das Skript die verwendeten Ressourcenbytes und
Hashes im Laufverzeichnis. Formatvalidierung prüft keine inhaltliche Granularität.
Der erste annotierte Fall bleibt Entwicklungsmaterial, keine unabhängige Evaluation.
