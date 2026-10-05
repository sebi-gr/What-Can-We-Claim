# Entwicklungsregeln

- Zu Beginn jeder Session zuerst `HANDOFF.md` und `WORKPLAN.md` lesen, danach `README.md` und den tatsächlichen Git-Stand prüfen. Veraltete Angaben als solche korrigieren.
- `HANDOFF.md` nach relevanten Entscheidungen, Änderungen und Prüfungen laufend aktualisieren, nicht erst am Sessionende. Auch bei einem spontanen Handoff müssen Stand, offene Punkte und nächster Schritt nachvollziehbar sein. Beschlüsse, Vorschläge und ungeprüfte Annahmen getrennt halten.
- `WORKPLAN.md` ist die maßgebliche Quelle für den aktuellen Arbeitsplan: Reihenfolge, Status, Abschlusskriterien und offene Planentscheidungen. Nach Fortschritt oder Planänderungen sofort aktualisieren, auch während einer Session und vor einem spontanen Handoff. Vorschläge ausdrücklich markieren; `HANDOFF.md` hält den überprüften Stand fest und verweist für den Plan auf `WORKPLAN.md`.
- `README.md` laufend mit dem tatsächlichen Code und Projektstand synchron halten. Bei Änderungen an Bedienung, Konfiguration, Voraussetzungen, Verhalten oder bekannten Grenzen die betroffenen Angaben und Beispiele im selben Arbeitsschritt aktualisieren. Geplante oder ungeprüfte Möglichkeiten ausdrücklich kennzeichnen; Detailplan in `WORKPLAN.md`, Übergabestand in `HANDOFF.md` belassen.
- **KISS:** Wir bauen einen kleinen Forschungsprototyp, um die Paper-RQs zu evaluieren und zu beantworten. Keine komplexe OSS-Plattform und kein Overengineering.
- Kleine, lesbare Skripte und explizite Ein-/Ausgaben bevorzugen. Minimal, aber verständlich: keine versteckte Logik oder komplizierten Abkürzungen, nur um Code zu verkürzen.
- Jede Funktion in `src/` erhält direkt oberhalb der Definition einen kurzen, verständlichen Block aus `#`-Kommentaren. Zweck, wesentliche Ein-/Ausgaben und relevante Nebenwirkungen oder Grenzen grob erklären; keine zeilenweise Nacherzählung. Kommentare bei Funktionsänderungen mitpflegen und auch bei neuen Funktionen ergänzen.
- Komponenten, Abhängigkeiten und Abstraktionen nur hinzufügen, wenn der nächste konkrete Versuch sie braucht. Keine vorsorglichen Frameworks, Plugin-Systeme oder allgemeinen Pipeline-Engines.
- Nur den beauftragten Schritt umsetzen. Bestehende Änderungen erhalten; keine beiläufigen Refactorings.
- LLM-Claim-Extraktion ist keine Wahrheitsprüfung. Modellübereinstimmung zählt nicht als unabhängige Evidenz. Originalaussagen, Unsicherheit, Negation und Voraussetzungen erhalten.
- Referenzmaterial, Fix, PoV und Fallmanifest aus dem Finding-Generator-Kontext ausschließen. Bei Agenten den tatsächlichen Toolzugriff begrenzen; getrennte Ordner allein reichen nicht.
- Reproduzierbarkeit durch fixierte Revisionen, Quellen, Hashes und gespeicherte Eingaben/Rohantworten herstellen. Leere Findings und Fehler dokumentieren; keine Wiederholung bis zum gewünschten Ergebnis.
- Keine Zugangsdaten oder privaten Gesprächsinhalte einchecken. Generierte Falldaten bleiben unversioniert; Herkunft und Lizenzen erhalten.

## Verzeichnis- und Namenskonvention

- Ausführbare Pipeline-Schritte liegen in `src/`, nummeriert nach Reihenfolge als `NN_verb_object.py` (zweistellig, englisch, snake_case): aktuell `01_prepare_case.py`, `02_generate_findings.py` und `03_decompose_findings.py`. Der manuelle Arbeitsschritt hat kein eigenes Skript.
- Tests liegen in `tests/` und heißen passend zum Schritt `test_NN_verb_object.py`. `tests/__init__.py` ermöglicht die Testsuche vom Repo-Wurzelverzeichnis.
- Prompts, Codebook, Schema und andere statische Hilfsdateien liegen in `resources/`. Pro Zweck genau eine aktuelle Datei ohne Versionssuffix; Ressourcenpfade relativ zur Skriptdatei auflösen.
- Keine parallelen Dokumentversionen oder fortlaufenden Änderungsjournale anlegen. README/WORKPLAN/HANDOFF halten Bedienung, Plan und aktuellen Stand knapp; Versionshistorie über Git. Unveränderte Ressourcen-Snapshots in Laufverzeichnissen sind Versuchsevidenz und bleiben erhalten.
- README, AGENTS, HANDOFF, WORKPLAN und LICENSE bleiben im Repo-Wurzelverzeichnis. Generierte Falldaten und Laufartefakte bleiben unter dem ignorierten `data/`.
- Lokale Zugangsdaten liegen in der ignorierten `.env` im Repo-Wurzelverzeichnis; nur die leere `.env.example` wird versioniert. Beide LLM-Schritte lesen `OPENAI_API_KEY` für die direkte OpenAI-API; die Prozessumgebung hat Vorrang. Keine Zugangsdaten in Modellkontext oder Laufartefakte übernehmen.
- CLI-Aufrufe erfolgen vom Repo-Wurzelverzeichnis: `python3 src/NN_verb_object.py`. Nummerierte Python-Module bei Bedarf mit `importlib.import_module` laden; keine zusätzlichen Wrapper oder Pipeline-Frameworks einführen.

## Prüfungen

Im Repo-Wurzelverzeichnis mit Python 3.9+; aktuell nur Standardbibliothek:

```bash
python3 -m unittest -v
git diff --check
```

Die Offline-Tests prüfen Fallvorbereitung, direkten OpenAI-Request, Kontexttrennung,
Byteerhalt/Hashes, Überschreibschutz, Fehler/Null-Ergebnisse ohne Retry, fehlenden
API-Key und `.env`-Laden ohne Zugangsdaten in Artefakten. Alte OpenRouter-Keys
werden nicht für OpenAI verwendet. Decomposer-Tests prüfen Felder, Unicode-/CRLF-
Zitate mit Vorkommen/Offsets, gemeinsame Zitate für unterschiedliche Claims/Familien
und Kontextreferenzen; keine Teilclaims bei ungültigen Ausgaben. Antworten sind
synthetische Fixtures, keine empirischen Ergebnisse. Der Windows-Symlink-Test wird
bei fehlendem Privileg ausdrücklich übersprungen; dort ist der Schutz ungeprüft.
Bei Codeänderungen ausführen; zusätzliche Tests nur für konkrete Risiken ergänzen.

Optionaler echter Vorbereitungslauf bei Änderungen am Download/Export (Netzzugriff auf `raw.githubusercontent.com`, Ziel muss neu sein):

```bash
python3 src/01_prepare_case.py --output data/VUL4J-18-check
```

Bestehende Versuchsdaten nicht löschen oder überschreiben; bei belegtem Ziel einen neuen Pfad wählen. Dieser Befehl führt **keinen Java-PoV** aus. Die separat ausgeführte Reproduktion mit dem vollständigen Benchmark und die verifizierten lokalen Build-/PoV-Befehle stehen in `resources/reproduce_vul4j18.md`; ihr Ergebnis belegt das getestete Mock-Forwarding-Verhalten, keinen End-to-End-Dateizugriff.
