# WORKPLAN — Claim-Pipeline

Stand: 2026-09-29. Maßgeblicher Plan; nur aktuellen Status, Beschlüsse und offene
Entscheidungen pflegen. Bedienung in README, überprüfter Übergabestand in HANDOFF.

## Ziel und Reihenfolge

Security-Findings in typisierte, einzeln prüfbare Behauptungen zerlegen und später
mit unabhängiger Evidenz bewerten. Arbeitsfragen: RQ-A Claim-Typen, RQ-B geeignete
Evidenz, RQ-C Korrektheit, Abdeckung, unentscheidbare Fälle und Prüfaufwand.
Die endgültige RQ-Fassung und Evaluationsplanung bleiben offen.

| Schritt | Stand | Abschlusskriterium |
|---|---|---|
| 1a. Fall vorbereiten | Erledigt | VUL4J-18 fixiert, Modellkontext/Referenzen getrennt, Herkunft und Hashes gespeichert. |
| 1b. Java-PoV reproduzieren | Erledigt | Verwundbar zwei erwartete Assertion-Fehler, gefixt zwei bestandene Tests; Befehle/Logs vorhanden. |
| 2. Review erzeugen | Technisch erledigt | Ein unverändertes Finding mit Eingaben, Rohantwort und Manifest gespeichert; Inhalt ungeprüft. |
| 3. Manuelle Zerlegung und Codebook | Erledigt als Entwicklungsbeispiel | 13 abgestimmte Claims; Regeln zu Propositionen, Familien und Bedingungen festgehalten. |
| 4. Automatische Zerlegung | In Arbeit | Formal gültige Claims und inhaltlich nachvollziehbare Aufteilung; bisherige Läufe noch zu grob. |
| 5. Entwicklungspilot erweitern | Vorschlag | Fallumfang, Einstellungen und Laufanzahl vorab festlegen. |
| 6. Unabhängige Verifikation evaluieren | Offen | Verfahren, Referenzbewertung, Evaluationsmenge und Metriken festlegen. |

## Beschlüsse

- KISS: drei kleine Python-Skripte, Standardbibliothek, explizite Ein-/Ausgaben.
  Keine Agenten-/Pipeline-Frameworks, Datenbank oder allgemeine Provider-Abstraktion.
- Ein aktuelles Dokument/Prompt pro Zweck ohne Versionssuffix. Änderungen direkt
  pflegen, Historie in Git. Laufartefakte mit Originalbytes/Hashes bleiben erhalten.
- OpenAI ersetzt OpenRouter in Generator und Decomposer. Key aus OPENAI_API_KEY
  in Umgebung oder .env; Modell und Tokenlimit explizit, kein Retry/Fallback.
  Ein Key-/Modellzugriff wird erst durch einen echten Lauf bestätigt.
- JSON-Format und lokale Validierung bleiben. Anbieterwechsel ist keine Zusage
  besserer Claims. Keine neue Promptstrategie oder Verifikation in diesem Auftrag.
- Ein Claim pro unabhängig prüfbarer Proposition, auch mehrere aus demselben Satz.
  Erst zerlegen, dann typisieren. Zitate dürfen mehrere unterschiedliche Claims
  belegen. Keine künstlichen Duplikate oder feste Claim-Anzahl.
- Vier Hauptfamilien: location, data_flow, protection_precondition,
  exploitability_impact (Untertypen exploitability/impact); other/unclear als Restfälle.
- Vollständige Aussagen mit Gegenstand; Positionen zuordnen. Bedingungen, Modalität,
  Negation, Alternativen und kausale Beziehungen erhalten. Redundanter Titel ohne
  Zusatzclaim, eigenständige Titelinformationen erfassen. Reines Parser-Verhalten
  ohne passende Hauptfamilie vorläufig other.
- Finding-Generator sieht nur die ausgewählten Quelldateien. Decomposer sieht nur
  Titel/Report, Prompt, Codebook und Schema. Referenzen und manuelle Annotationen
  bleiben außerhalb des Modellkontexts.
- Claim-Extraktion ist keine Wahrheitsprüfung. Modellübereinstimmung ist keine
  unabhängige Evidenz; PoV-Mocks beweisen keinen beliebigen Dateizugriff.

## Befund und nächster Schritt

Vorhandener Review: data/runs/VUL4J-18-review-001, ein Nemotron-Finding.
Decomposition 001: invalid_output wegen Zusatzfeldern. 002/003: completed,
je vier wortgleiche, zu grobe Propositionen; geänderte Anweisung brachte in 003
keinen Granularitätsgewinn. In 003 außerdem keine Kontext-IDs trotz This value.
Das sind Entwicklungsbefunde, keine allgemeine Aussage über das Modell.

OpenAI-Umstellung und Dateibereinigung implementiert und offline geprüft:
29 Tests, 28 bestanden/ein Windows-Symlink-Skip; CLI-Hilfen und git diff --check erfolgreich.
Noch kein echter OpenAI-Aufruf und kein überprüfter Claim-Qualitätsgewinn.

Nächster Vorschlag: einen bewusst geplanten OpenAI-Decomposer-Lauf mit dem
vorhandenen Finding, aktuellem Prompt/Codebook, explizitem Modell/Budget/Reasoning
und neuem Ausgabepfad ausführen. Aussagen, Bedingungen, Abdeckung und Kategorien
mit der manuellen Annotation und Lauf 003 vergleichen, ohne Zielanzahl oder
Wiederholung bis zum gewünschten Ergebnis. Ein neuer Generatorlauf ist dafür unnötig.

## Später offen

- Pilotumfang, Modelle, Reasoning-Einstellungen und Laufanzahl vorab bestimmen.
  Technische Fehler und Null-Ergebnisse mit auswerten.
- Je Claim-Familie passende Evidenz/Verifikatoren auswählen, etwa Quell-/AST-Prüfung,
  Datenflussanalyse, Konfigurations-/Kontrollflussprüfung oder ausführbare Tests.
  Die konkrete Toolwahl ist noch nicht beschlossen; OpenAnt ist nicht eingebunden.
- Unabhängig kuratierte Referenz und eigene Evaluationsmenge; Entwicklungsfall und
  assistierte Annotation nicht als unabhängigen Leistungsnachweis verwenden.
- Mögliche spätere Verifikationszustände: Supported, Contradicted, Inconclusive,
  Verification failure. Fehlgeschlagene Reproduktion widerlegt keine Schwachstelle.
