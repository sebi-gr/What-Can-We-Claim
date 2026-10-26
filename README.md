# What Can We Verify?

**Aktives Projekt ab 26.10.2026.** Nach dem POS-Entwicklungsexperiment konzentrieren
wir uns wieder auf begründete Zielclaims, Granularität und Claim-Erzeugung.
Vorhandene Technik bleibt erhalten; keine vollständige Verifikationsplattform geplant.

**Neuer Rechner / neue Codex-Session:** Zuerst [docs/RESTART.md](docs/RESTART.md)
lesen und das private Datenarchiv wiederherstellen. Danach
[HANDOFF.md](HANDOFF.md), [WORKPLAN.md](WORKPLAN.md) und
[Forschungsrichtung](docs/RESEARCH_DIRECTION.md). Der
[Startprompt](docs/NEXT_SESSION_PROMPT.md) enthält den konkreten nächsten Auftrag.

Kleiner Forschungsprototyp: Security-Findings eines LLM in einzeln prüfbare
Behauptungen zerlegen und später mit unabhängiger Evidenz prüfen.

## Stand

- VUL4J-18 / Apache JSPWiki vorbereitet; Java-PoV auf verwundbarer/gefixter Version
  reproduziert: zwei erwartete Assertion-Fehler gegenüber zwei bestandenen Tests.
  Das belegt das getestete Mock-Forwarding, keinen End-to-End-Dateizugriff.
- Ein Security-Finding erzeugt und manuell in 13 Claims zerlegt.
- Automatische Zerlegung technisch vorhanden. Die bisherigen Nemotron-Läufe 002/003
  lieferten je vier identische, zu grobe Propositionen. Formatgültigkeit belegt keine
  gute Zerlegung und keine Wahrheit der Claims.
- Generator und Decomposer verwenden jetzt direkt OpenAI. Ein echter OpenAI-Lauf
  mit dieser WCWV-Fassung und dessen Qualitätsvergleich stehen noch aus. Die
  separaten OpenAI-Pilotläufe in POS sind archiviert, keine WCWV-Qualitätsresultate.

Die folgenden Bedienhinweise beschreiben die unveränderten drei WCWV-Skripte.
Sie sind keine Freigabe für einen neuen Modelllauf. Die nächste Arbeitsphase
erstellt und prüft manuelle Zielbeispiele; die frühere 10-USD-Freigabe ist verbrauchs-
und versuchsbezogen auf den abgeschlossenen POS-Pilot begrenzt.

Arbeitsplan: [WORKPLAN.md](WORKPLAN.md). Übergabestand: [HANDOFF.md](HANDOFF.md).

## Dateien

```text
src/
  01_prepare_case.py
  02_generate_findings.py
  03_decompose_findings.py
tests/
  test_01_prepare_case.py
  test_02_generate_findings.py
  test_03_decompose_findings.py
resources/
  review_prompt.txt
  decomposition_prompt.txt
  claim_codebook.md
  claim_response_schema.json
  manual_annotation_template.md
  reproduce_vul4j18.md
data/                         # lokale Versuchsdaten, von Git ignoriert
```

Pro Dokument/Prompt eine aktuelle Datei ohne Versionssuffix; die Historie liegt
in Git. Gestartete Modellläufe speichern ihre tatsächlich verwendeten Eingaben,
Ressourcen und Rohantworten separat unter `data/`. Diese Laufkopien bleiben erhalten.

## Einrichtung

Python 3.9+, nur Standardbibliothek. Alle Befehle vom Repo-Wurzelverzeichnis ausführen.
Unter Windows kann statt `python3` beispielsweise `python3.14.exe` verwendet werden.

In der lokalen, ignorierten `.env`:

```dotenv
OPENAI_API_KEY=dein_api_key
```

`.env.example` enthält nur den leeren Eintrag. Ein nichtleerer `OPENAI_API_KEY`
aus der Prozessumgebung hat Vorrang. Keine Übergabe des Keys als CLI-Argument nötig.
Der einfache Loader akzeptiert unzitierte oder vollständig einfach/doppelt zitierte
Werte; keine Variablenexpansion oder Inline-Kommentare hinter dem Wert.

Beide LLM-Schritte senden genau einen Request an
`https://api.openai.com/v1/chat/completions`. Modell und Tokenlimit sind explizite
CLI-Argumente. Es gibt keine automatische Modellwahl, Fallbacks, Tools oder Retries.
OpenAI-Aufrufe können Kosten verursachen; die frühere Beschränkung auf kostenlose
OpenRouter-Modelle entfällt. Das Tokenlimit ist kein Geldbudget.

`--max-output-tokens` setzt `max_completion_tokens` einschließlich Reasoning.
Ohne `--no-reasoning` bleibt die Reasoning-Einstellung beim Modellstandard;
mit dem Flag wird `reasoning_effort=none` gesendet. Das ausgewählte Modell muss
`none` unterstützen. Requests nutzen JSON-Modus und `store=false`; die Prüfung
des konkreten Claim-Formats erfolgt lokal.
[OpenAI API-Vertrag](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create).

Die Beispiele verwenden `gpt-6-luna`, dessen Dokumentation Chat Completions und
Reasoning `none` ausweist. Das ist eine Beispielwahl, keine geprüfte Qualitäts-
oder Zugriffsbestätigung für diesen Key. Ein anderes kompatibles OpenAI-Modell
kann explizit angegeben werden; OpenRouter-IDs wie `anbieter/modell:free` werden
abgelehnt. Modell-Snapshots nutzen, soweit verfügbar; angeforderte und zurückgegebene
Modellkennung werden gespeichert.
[Modelldokumentation](https://developers.openai.com/api/docs/models/gpt-6-luna).

## 1. Fall vorbereiten

```bash
python3 src/01_prepare_case.py --output data/VUL4J-18
```

Lädt fixierte Revisionen von `raw.githubusercontent.com`. Unter `model_input/`
liegen fünf unveränderte Quell-/Konfigurationsdateien: WikiServlet,
DefaultURLConstructor, URLConstructor, jspwiki.properties und web.xml.
`reference/` enthält Dataset-Zeile, Fix, PoV und Lizenzhinweise. `manifest.json`
speichert Revisionen und Hashes. Ein belegtes Ziel wird nicht überschrieben.

Nur `model_input/` darf an den Finding-Generator gehen. Fix, PoV, Manifest,
Annotationen und Projektdokumentation bleiben außerhalb seines Kontexts.
Der Ausschnitt ist kein vollständiger Build und erlaubt keine Aussagen über
fehlende Filter, Aufrufer oder ein tatsächliches Deployment. Agenten mit Tools
benötigten zusätzlich eine technische Beschränkung des Dateizugriffs.

Dieser Vorbereitungsschritt führt keinen Java-Test aus. Die bereits geprüften
Build-/PoV-Befehle und ihre Grenzen stehen in
[reproduce_vul4j18.md](resources/reproduce_vul4j18.md).

## 2. Finding erzeugen

```bash
python3 src/02_generate_findings.py --model gpt-6-luna --max-output-tokens 8192 --no-reasoning --output data/runs/VUL4J-18-openai-001
```

Standardkontext: `data/VUL4J-18/model_input/`, alternativ `--model-input PFAD`.
Gesendet werden ausschließlich die fünf erlaubten Dateien mit Pfaden und
Originalzeilennummern sowie [review_prompt.txt](resources/review_prompt.txt).
Symlink-Pfade werden abgelehnt. Keine externe Recherche oder Toolausführung.

## 3. Manuell zerlegen

Regeln: [claim_codebook.md](resources/claim_codebook.md). Die
[Vorlage](resources/manual_annotation_template.md) für neue Annotationen nach
`data/annotations/` kopieren. Das bestehende Entwicklungsbeispiel liegt unter
`data/annotations/VUL4J-18-review-001/manual_annotation_001.md`.

Ein Satz kann mehrere unabhängig prüfbare Propositionen mit verschiedenen Familien
enthalten. Dasselbe Zitat darf mehrfach verwendet werden. Keine Duplikate allein
zum Wechseln der Familie und keine feste Zielanzahl. Bedingungen, Unsicherheit,
Negation, Alternativen und Zusammenhänge erhalten. Ein redundanter Titel braucht
keinen zusätzlichen Claim. Die manuelle Annotation entstand mit Vorwissen über
Code/Fix/PoV und Codex-Unterstützung; sie ist keine unabhängige Wahrheitsreferenz.

## 4. Gespeichertes Finding automatisch zerlegen

Das vorhandene Finding kann direkt weiterverwendet werden; kein neuer Review nötig:

```bash
python3 src/03_decompose_findings.py --findings data/runs/VUL4J-18-review-001/findings.jsonl --finding-id 0721c0a0-bba7-48c1-a63c-da196a69d97c:F001 --model gpt-6-luna --max-output-tokens 8192 --no-reasoning --output data/decompositions/VUL4J-18-openai-001
```

Frischer Kontext nur aus ausgewähltem Titel/Report,
[decomposition_prompt.txt](resources/decomposition_prompt.txt), Codebook und
[claim_response_schema.json](resources/claim_response_schema.json).
Keine manuelle Annotation, Quell-/Referenzdateien oder Nachbarfindings im Request.
Das Schema enthält weiterhin `schema_version: "1"` als Datenformatkennung;
das ist keine zusätzliche Dokumentversion.

Claims enthalten Proposition, Familie/Untertyp/Begründung, Qualifiers, exakte Zitate
mit einsbasierter Vorkommensnummer und lokale Kontext-IDs. Der Wrapper ergänzt
nullbasierte Unicode-Codepoint-Offsets (Ende exklusiv), Run-/Finding-ID und
`verification_status: not_evaluated`. Er prüft Felder, Kategorien, Zitate und
Referenzen, aber keine Granularität, Vollständigkeit oder Wahrheit.

## Laufartefakte und Fehler

| Datei | Zweck |
|---|---|
| `request.json` | Tatsächlich gesendeter Body, ohne Authorization-Header |
| `generation_raw.json` / `decomposition_raw.json` | Unveränderte empfangene Antwort |
| `run_manifest.json` | Modell, Parameter, Status, Zeit, Usage, Eingabe-/Ressourcen-/Codehashes |
| `findings.jsonl` / `claims.jsonl` | Nur vollständig gültige Ausgaben |
| `validation.json` | Beim Decomposer: Format-/Zitat-/Referenzprüfung und erster Fehler |
| Eingaben und Ressourcen | Exakte Quell-, Finding-, Prompt-, Codebook- und Schemakopien je Schritt |

`completed` bedeutet formal gültig. Gültige leere Listen werden als `no_findings`
bzw. `no_claims` gespeichert. Ungültige oder abgeschnittene Antworten ergeben
`invalid_output`, technische/API-/Konfigurationsfehler `run_error`. Fehler und leere
Ergebnisse erhalten; keine Teilclaims, automatische Reparatur oder Wiederholung.
Bei Fehlern zeigen CLI und Manifest die Ursache; Exit-Code 1. Vorzeitig beendete
Prozesse können unvollständige Artefakte hinterlassen. Bestehende Ziele bleiben erhalten.

Usage wird unverändert gespeichert; `cost_usd` wird nicht berechnet und bleibt
`null`. Niemals `.env` oder Authorization-Header weitergeben oder versionieren.
Der Anbieterwechsel allein beweist keine bessere Zerlegung; das nächste Ergebnis
mit den bisherigen Propositionen und der manuellen Annotation vergleichen.

## Prüfungen

```bash
python3 -m unittest -v
git diff --check
```

Offline-Tests mit synthetischen Antworten: API-Vertrag, Kontexttrennung,
Key-Laden/Geheimnisschutz, Hashes, Überschreibschutz, Fehler ohne Retry sowie
Claim-Format, Zitate/Offsets und Referenzen. Der Symlink-Test wird unter Windows
bei fehlendem Privileg ausdrücklich übersprungen; der Schutz ist dort dann ungeprüft.
Ein echter API-Aufruf oder Java-Build ist nicht Bestandteil der Python-Tests.
