# HANDOFF — aktueller Stand

Stand: 2026-10-05. WIP-Übergabe der Implementierung und bereinigten Dokumentation
auf Branch main, aufbauend auf 8f9b25e. Commit-Nachricht:
`wip: handoff for prose or structure repo`. Der verbindliche nächste Schritt
steht in WORKPLAN.md; Commit-/Remote-Stand über Git prüfen.

## Implementierung

- src/01_prepare_case.py: fixierter VUL4J-18-Export, Modellkontext/Referenzen getrennt.
- src/02_generate_findings.py und src/03_decompose_findings.py: direkt OpenAI Chat
  Completions über Standardbibliothek, OPENAI_API_KEY aus Umgebung/.env.
  Vorhandener .env-Eintrag geprüft, Wert nicht ausgegeben und Datei nicht geändert.
- OpenRouter-spezifische Preis-/Routing-/Pluginparameter entfernt; explizites Modell,
  max_completion_tokens, JSON-Modus und store=false. --no-reasoning setzt
  reasoning_effort=none; ohne Flag Modellstandard. Keine automatischen Wiederholungen.
- Ressourcen auf einen aktuellen Namen je Zweck reduziert: review_prompt.txt,
  decomposition_prompt.txt, claim_codebook.md, claim_response_schema.json.
  Codebook historienfrei konsolidiert, Regeln für feine Propositionen erhalten.
  README/WORKPLAN/HANDOFF gekürzt, AGENTS legt stabile Dateinamen fest.
- Schema-Version 1 bleibt Datenformatkennung. Historische Modellläufe behalten
  ihre ursprünglichen Dateinamen, Ressourcenbytes und Hashes. Bestehende manuelle
  Annotationen/Reviews und Java-PoV-Artefakte bleiben Versuchsdaten unter data/.

## Überprüfter Forschungsstand

- Java-PoV: zwei erwartete Assertion-Fehler verwundbar, zwei bestandene Tests gefixt.
  Nur Mock-Forwarding belegt; Reproduktionsbefehle in resources/reproduce_vul4j18.md.
- Review 0721c0a0-bba7-48c1-a63c-da196a69d97c unter data/runs/VUL4J-18-review-001:
  ein Finding, damals Nemotron/OpenRouter ohne Reasoning; Aussagen ungeprüft.
- Manuelle Annotation: 13 abgestimmte Entwicklungsclaims, Codex-Unterstützung und
  Vorwissen über Code/Fix/PoV dokumentiert. Keine unabhängige Wahrheitsreferenz.
- Decomposition 001 ungültig; 002 und 003 formal gültig mit vier wortgleichen
  Satz-Propositionen. Feinere Granularität nicht erreicht, in 003 alle Kontext-IDs leer.
  Letzter Lauf: c939bbd8-090a-4c51-b14d-998d1fc8653c. Formatgültigkeit ist kein Qualitätsurteil.

## Prüfungen und offene Punkte

Für die WIP-Übergabe am 05.10.2026 erneut geprüft: 29 Offline-Tests, davon
28 bestanden und ein bestehender Windows-
Symlink-Skip. Beide CLI-Hilfen und git diff --check erfolgreich. Kein echter
API-Aufruf oder Java-Neulauf. .env und gespeicherte Versuchsartefakte per Hash
unverändert; Fallvorbereitung und PoV-Dokumentation unverändert.
API-Vertrag anhand offizieller OpenAI-Dokumentation geprüft. Verfügbarkeit/Zugriff
für den lokalen Key und Extraktionsqualität bleiben ungeprüft. Beispiele verwenden
explizit gpt-6-luna; kein Modell im Code fest voreingestellt.
Nächster Vorschlag: ein neuer OpenAI-Decomposer-Lauf mit vorhandenem Finding und
frischem Ziel; anschließend Inhaltsvergleich, keine automatische Wiederholung.
