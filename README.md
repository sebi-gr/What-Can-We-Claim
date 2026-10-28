# What Can We Claim?

*Generating Security Claims from Code and Prose with LLMs*

Minimaler Entwicklungsvergleich mit drei Vul4J-Fällen:

- **Direkt:** Code → Claims → Vergleich mit vorher fixierten Zielclaims.
- **Prosa:** Derselbe Code → kurzer Report → Claims → dieselbe Zielreferenz.

Die [Basisclaims](examples/jspwiki/baseline.json) stehen je Fall unter `examples/<fall>/baseline.json` (JSPWiki, Jackson XML, Commons YAML). Sie wurden vor den neuen Modelloutputs nach dem Muster der [Originalannotation von SG](examples/jspwiki/manual/manual_annotation_submitted_001.md) und der [assistierten Revision](examples/jspwiki/manual/manual_annotation_001.md) erstellt. Es sind KI-unterstützte Entwicklungsreferenzen; fachliches menschliches Gegenlesen steht aus.

## Ausführen

Python 3.10+, für die Erzeugung nur Standardbibliothek. `OPENAI_API_KEY` aus der Prozessumgebung oder der ignorierten `.env`; keine Schlüssel in Artefakten.

```bash
python3 -m unittest -v
python3 run.py --dry-run --budget-usd 1
python3 run.py --output results/run-001 --budget-usd 1
```

Der Lauf nutzt `gpt-5.4-mini-2026-03-17`, neun zustandslose Aufrufe, maximal 8.192 Ausgabetokens für Claims bzw. 2.048 für Reports. Kein Retry, kein Überschreiben, kein Modellwechsel. Der erste Befehl mit `--dry-run` verursacht keine API-Kosten; ein echter Lauf braucht einen neuen Ausgabeordner und einen freigegebenen Kostenrahmen. Die Vorabprüfung reserviert konservativ höchstens 1 USD für diesen Versuch.

[Prompts](resources/prompts.json), [Claimformat](resources/claim_schema.json), [Zerlegungsregeln](resources/claim_codebook.md) und [manuelle Vorlage](resources/manual_annotation_template.md) sind explizit. An die Modelle gehen ausschließlich erlaubte Codedateien bzw. beim Extraktor der neue Report; keine Basisclaims, alten Reports, Fixes, PoVs oder Datasetlabels. Syntax-, Zitat- und Referenzprüfung beweisen keine Claimwahrheit.

## Ergebnisse und Bericht

`results/run-001/` enthält die fixierten Referenzen, exakten Requests/Rohantworten, generierte Claims und Reports sowie ein kleines Laufmanifest. `review.json` hält die einzeln begründete inhaltliche Zuordnung fest. Diese Bewertung ist von Codex ausgearbeitet, kein automatisches Matching und kein unabhängiges menschliches Review. Die drei bekannten Entwicklungsfälle erlauben keine generelle Überlegenheitsaussage.

```bash
python3 -m pip install -r requirements.txt
python3 make_pdf.py --run results/run-001 --output output/pdf/wcwc-ergebnisse.pdf
```

Die [dreiseitige Zusammenfassung](output/pdf/wcwc-ergebnisse.pdf) beschreibt Motivation, Architektur, Zielclaims und tatsächliche Ergebnisse. [Quellen/Herkunft](examples/sources.json), [Literatur und Fallauswahl](resources/references.json) sowie die [frühere Entwicklungsnotiz](examples/reference.md) bleiben nachvollziehbar. Für die Fremdquellen gelten die jeweiligen LICENSE-/NOTICE-Dateien.
