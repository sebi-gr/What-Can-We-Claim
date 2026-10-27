# Review des ersten manuellen Entwurfs

Datum: 2026-09-24. Annotator: SG. Review: Codex.
**Status: Formulierungsvorschläge am 24.09.2026 auf Nutzerauftrag in die
[Arbeitsfassung](manual_annotation_001.md) übernommen (13 Claims).**
Die folgenden Befunde beziehen sich auf den ursprünglichen Entwurf mit zwölf Claims.
Sie bleiben als Review-Verlauf erhalten. Die vier Codebook-Präzisierungen wurden
inzwischen vom Nutzer bestätigt und in v0.2 übernommen; die Übernahme ist kein Urteil über die Wahrheit der Claims.
Gegenstand sind Extraktionstreue, Aufteilung und Typisierung nach
[Codebook v0.1](../../../resources/claim_codebook_v0_1.md), nicht die Wahrheit der Claims.
Dieses assistierte Review ist keine unabhängige zweite menschliche Annotation.

## Grundlage und erhaltene Dateien

- [Originalabgabe](manual_annotation_submitted_001.md): bytegleiche Sicherung der
  ausgefüllten `resources/manual_annotation_template.md`, einschließlich Platzhaltern.
- SHA-256 der Originalabgabe: `893ee3ef9ea79fefb3d73cb9e856dc80822698534f6a6f4b3d75bcf57496113f`.
- [Arbeitsfassung](manual_annotation_001.md): inzwischen 13 überarbeitete Claims
  mit Herkunft, Originalfinding und Abdeckung.
- [Finding](../../runs/VUL4J-18-review-001/findings.jsonl):
  `0721c0a0-bba7-48c1-a63c-da196a69d97c:F001`.
- SHA-256 der Finding-Datei: `ac2711de8101111aa23a0861553cfe60489fa40393dc4806fc5e2b0bd794308a`.

Die generische Vorlage in `resources/` ist wieder leer. Das ursprüngliche
vorbereitete Arbeitsblatt `manual_annotation.md` bleibt ebenfalls erhalten.
Weiterarbeiten in `manual_annotation_001.md`; die Originalabgabe bleibt unverändert.

## Befund

Alle zwölf Originalzitate sind exakte Ausschnitte des Findings. Titel und sämtliche
vier Reportsätze kommen darin vor. Das belegt die Textzuordnung, noch nicht die
vollständige oder bedeutungstreue Zerlegung der darin enthaltenen Behauptungen.

C04 ist als Datenflussaussage weitgehend eigenständig und originalgetreu. C09 erhält
bereits „could“, „potentially“ und die beiden alternativen Wirkungen. Überarbeiten
müssen wir vor allem unvollständige Satzteile, die Titelklassifikation und C11/C12.
Es gibt keine vorgegebene richtige Claim-Anzahl.

## Rückmeldung je Claim

| Claim | Extraktion / Aufteilung | Typisierung / Vorschlag |
|---|---|---|
| C01 | Der Titel behauptet eine Schwachstelle, aber bezeichnet `WikiServlet` nicht genauer als „Anwendung/Funktion“. Diese Auswahl nicht hinzufügen. Mit C02 als eine Titelaussage behandeln. | `location` erfasst eine Codeoperation/-position, nicht automatisch eine Schwachstellenbehauptung mit Ortsnamen. Vorschlag: zusammengefasster Titel vorläufig `other`, Begründung „Schwachstellenlabel“; Codebook-Grenzfall. |
| C02 | „ausnutzbar“ macht aus dem knappen „via PathInfo“ eine explizite Ausnutzbarkeitsaussage. Für einen konkreten Angriff ist der Report S3 die bessere Quelle. | Ein über PathInfo möglicher Angriff ist nicht allein wegen des Parameternamens `data_flow`. Mit C01 zusammenführen; konkreten Angriff in C09 behandeln. |
| C03 | S1 lokalisiert die Verwendung der Methode in Zeile 89. „Die Schwachstelle befindet sich dort“ verengt die gesamte Schwachstelle auf diese Stelle. Die benannte Operation lokalisieren. | `location` passt nach dieser Präzisierung. Alternativ die Position als Bestandteil von C04 erhalten. |
| C04 | Inhaltlich weitgehend treu: Methode extrahiert Seitennamen aus `request.pathInfo`. Quellenfeld `report`, S1 ergänzen. | `data_flow` passt: Herkunft des extrahierten Werts. Eine kurze Begründung ergänzen. |
| C05 | „Without sufficient validation“ ist ohne Gegenstand kein eigenständig verständlicher Claim. Methode, Eingabe und Extraktion aus S1 wieder aufnehmen. „Nicht ausreichend“ nicht zu „gar nicht“ verstärken. | `protection_precondition` passt; die Verneinung und ihr Bezug fehlen im Zusatzfeld „keine“. |
| C06 | „This value“ ist unaufgelöst, und die Verwendung ist nicht konkret benannt. S1 als zusätzliche Quelle nötig. Kann mit C07 verbunden werden; Zeilen 97–98 bleiben dabei erhalten. | Als eigenständige Positionsaussage nur mit benannter Operation sinnvoll. Nicht allein wegen einer Zeilennummer einen Claim erzeugen. |
| C07 | Satzfragment ohne Subjekt; „it“ muss aus S1/S2 aufgelöst werden. Vollständigen Datenfluss formulieren. | `data_flow` passt. Bezug auf den in C04 beschriebenen Seitennamen dokumentieren. |
| C08 | „without sanitization“ braucht Eingabe und Operation. Nicht auf die gesamte Anwendung ausweiten. | `protection_precondition` passt; behauptetes Fehlen der Sanitization und dessen Geltungsbereich festhalten. |
| C09 | Ganzer Satz treu übernommen, aber Request-Konstruktion und mögliche Folgen sind getrennt beurteilbar. Vorschlag: Konstruktion und bedingte Wirkung trennen; Modalität und „oder“ erhalten. | `exploitability_impact` grundsätzlich passend. Untertypen und die Beziehung der Teilclaims ergänzen; das Konstruieren allein behauptet noch keinen erfolgreichen Angriff. |
| C10 | „(lines 245-268)“ ist eine Fundstellenangabe ohne Proposition. Der Report ordnet sie `DefaultURLConstructor.parsePageFromURL` zu. | Als Codeposition an die entsprechenden Aussagen aus C11 hängen. Nur bei eigenständiger Aussage über die Methodenposition wäre `location` ein separater Claim. |
| C11 | Vermischt Slash-Entfernung, fehlendes Dekodieren, fehlende Validierung und eine kausale Weiterleitungsbehauptung. Methodenname und „only“ fehlen; „in the servlet“ ist doppelt. Siehe Vorschläge unten. | Nicht pauschal alles `protection_precondition`: Verhalten der Methode, fehlende Schutzbehandlung und Weiterleitungsbeziehung unterscheiden. |
| C12 | Die Wirkung ist als möglich erhalten, aber Bezugsereignis und JSP-Bedingung fehlen in der Proposition. Die Bedingung steht bereits richtig im Zusatzfeld und muss auch in den Claim selbst. | `exploitability_impact`, Untertyp `impact`, passt. Alternativen und unbestimmte „further exploitation“ unverändert lassen, keinen konkreten Folgeangriff ergänzen. |

## Konkrete Formulierungsvorschläge

Die Kennungen unten beziehen sich auf den ursprünglichen Entwurf; a/b usw.
kennzeichnen die inzwischen übernommene Aufteilung. Die Formulierungen wurden zur
Übernahme freigegeben, ihre Wahrheit bleibt ungeprüft. Behauptete Codepositionen
werden aus dem Finding übernommen, nicht anhand des Programmcodes korrigiert.

- **C01 + C02:** „In WikiServlet besteht eine Path-Traversal-Schwachstelle über
  PathInfo.“ Quelle: `title`, T. Eine Titelaussage statt zwei unterstellter
  Detailaussagen. Vorläufig `other` mit Begründung „Schwachstellenlabel“.
- **C03, falls separat:** „In WikiServlet.java Zeile 89 wird
  DefaultURLConstructor.parsePageFromURL zur Extraktion des Seitennamens verwendet.“
  Quelle: `report`, S1; `location`.
- **C05:** „DefaultURLConstructor.parsePageFromURL extrahiert den Seitennamen
  aus request.pathInfo ohne ausreichende Validierung.“ Quelle: `report`, S1;
  `protection_precondition`.
- **C06 + C07:** „Der aus request.pathInfo extrahierte Seitenname wird in
  WikiServlet.java Zeilen 97–98 direkt mit der URL verkettet, um einen
  Forward-Request-Dispatcher zu erzeugen.“ Quellen: `report`, S1 und S2;
  `data_flow`, Kontext C04. Die Position bleibt in der Aussage erhalten.
- **C08:** „Der aus request.pathInfo extrahierte Seitenname wird beim Erzeugen
  des Forward-Request-Dispatchers ohne Sanitization mit der URL verkettet.“
  Quellen: `report`, S1 und S2; `protection_precondition`, Kontext C04/C07.
- **C09a:** „Ein Angreifer könnte einen Request konstruieren, dessen pathInfo
  Verzeichnistraversalsequenzen wie '../../etc/passwd' enthält.“ Quelle: `report`,
  S3; `exploitability_impact` / `exploitability` als behaupteter Angriffsschritt.
- **C09b:** „Mit einem solchen Request könnte ein Angreifer möglicherweise auf
  nicht autorisierte Ressourcen zugreifen oder vorgesehene Zugriffskontrollen
  umgehen.“ Quelle: `report`, S3; `exploitability_impact` / `impact`, Kontext C09a.
  Die zwei alternativen Wirkungen bleiben unter derselben Möglichkeitsaussage.
- **C11a mit C10:** „DefaultURLConstructor.parsePageFromURL (Zeilen 245–268)
  entfernt nur einen führenden Slash.“ Quelle: `report`, S4. Vorläufig `other`
  für reines Parser-Verhalten: Die bisherigen Familien bilden Transformationen
  ohne explizite Schutz-/Flussbehauptung nicht eindeutig ab. Grenzfall notieren.
- **C11b:** „DefaultURLConstructor.parsePageFromURL dekodiert den Pfad nicht
  weiter.“ Quelle: `report`, S4. Vorschlag: `protection_precondition` im Kontext
  der behaupteten unzureichenden Eingabebehandlung; die Zuordnung ist zu begründen.
  Daraus folgt nicht, dass Dekodieren allgemein eine Schutzmaßnahme wäre.
- **C11c:** „DefaultURLConstructor.parsePageFromURL validiert den Pfad nicht
  weiter.“ Quelle: `report`, S4; `protection_precondition`.
- **C11d:** „Das Fehlen zusätzlicher Prüfungen im Servlet ermöglicht die
  Weiterleitung bösartiger Pfadsequenzen an interne JSPs.“ Quelle: `report`, S4;
  Vorschlag `data_flow` mit expliziter Ursache. Die behauptete Kausalbeziehung
  nicht durch zwei unverbundene Sätze verlieren. „Zusätzliche“ nicht zu
  „überhaupt keine Prüfungen“ verstärken.
- **C12:** „Die Weiterleitung bösartiger Pfadsequenzen an interne JSPs könnte zu
  Informationspreisgabe oder weiterer Ausnutzung führen, abhängig von der
  Verarbeitung des 'page'-Parameters durch die Ziel-JSP.“ Quelle: `report`, S4;
  `exploitability_impact` / `impact`, Kontext der Weiterleitungsbehauptung aus C11.

## Abdeckung und noch offene Felder

Zuordnung der **ursprünglichen zwölf Claims nach ihren Zitaten**, noch keine
Bestätigung der vollständigen Propositionen:

| Passage | Entwurfs-Claims | Nach Überarbeitung prüfen |
|---|---|---|
| T | C01, C02 | Eine Titelaussage; keine zusätzlichen Mechanismus-/Erfolgsannahmen. |
| S1 | C03, C04, C05 | Aufrufposition, Herkunft des Seitennamens, unzureichende Validierung. |
| S2 | C06, C07, C08 | Wertbezug auf S1, Verkettung/Dispatcher, fehlende Sanitization. |
| S3 | C09 | Request-Konstruktion, mögliche alternative Folgen, Beispielpayload. |
| S4 | C10, C11, C12 | Methodenposition, „only“, beide Negationen, fehlende zusätzliche Prüfungen als Ursache, Weiterleitung, bedingte alternative Wirkung. |

Im Arbeitsblatt fehlen noch Quellenfelder/Satzkennungen, Familienbegründungen,
benötigte Kontextbezüge. Zusätzliche Prüffelder werden nach der späteren
Formularvereinfachung nicht mehr verlangt. „Keine“ ist bei
fehlender Validierung oder Sanitization als Negationsangabe nicht passend;
„weitere Voraussetzungen nicht genannt“ wäre davon getrennt zu notieren.
Die Abschluss-Checkboxen und der Abdeckungscheck sind noch offen.

## Codebook-Präzisierungen zur Entscheidung

Am 24.09.2026 bestätigt und in v0.2 aufgenommen; v0.1 bleibt erhalten:

1. Ein Claim muss Gegenstand und Aussage enthalten. Zeilennummern sind meist
   Fundstellen; „without sanitization“ braucht die zugehörige Operation.
2. Schwachstellenlabel im Titel nicht allein aufgrund eines Orts-/Parameternamens
   als `location`/`data_flow` typisieren. Vorläufig `other` mit Begründung zulassen.
3. Reines Parser-Verhalten ist ein Restfall des bisherigen Schemas. Für den
   Pilot `other` nutzen; noch keine neue Familie aufgrund dieses Einzelfalls erzwingen.
4. Einschränkungen müssen in der Proposition erhalten bleiben, auch wenn sie
   zusätzlich in einem Qualifier-Feld stehen. Nach einer Aufteilung die Kausalität,
   Modalität und Alternativen erneut prüfen.

**Nächster Schritt:** Die Formulierungen sind übernommen, Abdeckung und Kontext
in der Arbeitsfassung ergänzt. Die Codebook-Präzisierungen sind bestätigt und Schritt 3 ist abgeschlossen.
Als Nächstes folgt Schritt 4; dessen Umsetzung wurde noch nicht begonnen.
