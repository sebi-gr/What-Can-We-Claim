# Handoff: Weiterarbeit in What Can We Verify

Stand: 26.10.2026. **Dieses Repository ist wieder das aktive Forschungsprojekt.**
Verbindliche Reihenfolge: [WORKPLAN.md](WORKPLAN.md). Rechnerwechsel:
[docs/RESTART.md](docs/RESTART.md). Starttext: [docs/NEXT_SESSION_PROMPT.md](docs/NEXT_SESSION_PROMPT.md).

## Entscheidung und nächster Schritt

Nach der Besprechung mit Andreas und der ausdrücklichen Entscheidung des Nutzers
kehren wir zur beispielorientierten Claim-Erzeugung zurück. Zunächst den Nutzen
begründet motivieren, Zielclaims für unterschiedliche Codebeispiele ausarbeiten,
fachlich gegenlesen lassen und Abstraktionsniveau/semantische Zuordnung klären.
P/D aus POS ist nützliches Material, aber kein Auftrag, sofort eine große Studie,
CodeQL-Pipeline, Nutzerstudie oder ein allgemeines Verifikationssystem zu bauen.

Als Nächstes das historische JSPWiki-Beispiel erneut bearbeiten: Reportreferenz
und begründete Codereferenz nebeneinander. Danach zwei andere Entwicklungsbeispiele
ergänzen. KI-Unterstützung und Vorwissen kenntlich machen. Noch kein neuer Modelllauf.
Ausführliche Einordnung: [Forschungsrichtung](docs/RESEARCH_DIRECTION.md).

## Tatsächlicher Implementierungsstand

- Drei aktive Skripte: Fallvorbereitung, Reportgenerierung und Reportzerlegung.
- Direkte OpenAI-Aufrufe über Standardbibliothek; Modell und Tokenlimit explizit,
  keine Retries. Standalone-Aufrufe haben keinen monetären Schutz.
- WCWV-Antwortvertrag bleibt schema_version=1. POS-Profil 0.1 wurde nicht importiert.
- Vorhandenes JSPWiki-Finding: Run 0721c0a0-bba7-48c1-a63c-da196a69d97c.
- 13 historische manuelle Claims: SG mit Codex-Unterstützung und Vorwissen über
  Code/Fix/PoV; Reportzerlegung, keine unabhängige Wahrheitsreferenz.
- Historische Decomposition 001 ungültig; 002/003 je vier wortgleiche, zu grobe
  Satzpropositionen. In 003 leere Kontext-IDs. Originalantworten bleiben erhalten.
- Historischer Java-PoV: zwei erwartete Assertion-Fehler verwundbar, zwei bestandene
  Tests mit Fix. Nur Mock-Forwarding, kein allgemeiner Exploitnachweis.

## Sicherung und Wiederherstellung

Das private Repository https://github.com/sebi-gr/wcwv-handover-20261026 enthält:

- unverändertes ASR-Transkript und Todos der Andreas-Besprechung;
- WCWV-Daten einschließlich Annotationen/Reviews, Decomposition-Rohdaten und PoV-Logs;
- POS-Quellstand und dessen vollständige lokale Forschungsdaten;
- Git-Bundles beider Projekte einschließlich lokaler Branches/Tags;
- Dateihashes, dokumentierte Ausschlüsse und einen geprüften Wiederherstellungshelfer.

Nach `restore.py --wcwv ...` liegen ursprüngliche WCWV-Daten unter `data/` und
POS unter `archive/prose-or-structure/`. Öffentliches WCWV allein enthält diese
Daten nicht. Die Ablagen sind weiterhin ignoriert. Das private Archiv muss erhalten
bleiben, auch wenn die alte POS-Arbeitskopie oder der POS-Remote gelöscht wird.
Niemals das private Transkript öffentlich einchecken.

POS brachte Profil-/Annotationsregeln, Literaturabgrenzung, weitere Beispiele und
einen technischen Pilot mit 76/82 formal erfolgreichen Aufgaben hervor. Keine
menschlichen Qualitätsurteile liegen vor. Siehe [POS_LESSONS.md](docs/POS_LESSONS.md).

## Grenzen und Freigaben

Kein neuer Java-PoV oder API-Lauf in dieser Übergabe. Alte Daten nicht überschreiben.
Die 10-USD-Freigabe war nur für den POS-Pilot vom 06.10.2026. Für spätere Läufe
Modell, Preise, Tokenlimit und neue Kostenfreigabe festlegen. Keine Zugangsdaten
übertragen; `.env` am Ziel bei Bedarf neu anlegen.

Übergabe-Teststand am 26.10.2026: alle 29 WCWV-Offline-Tests und alle 106 POS-Tests
bestanden, ohne Skip. Der frühere WCWV-Stand hatte einen Windows-Symlink-Skip.
Wiederherstellungsnachweise werden im privaten Archiv unter `validation/`
festgehalten. Ein Skip auf einem anderen Rechner belegt keinen Symlink-Schutz.
Ausführung vom Repo-Wurzelverzeichnis: `python -X utf8 -m unittest -v`,
anschließend `git diff --check`.
