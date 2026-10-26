# Was aus Prose or Structure erhalten bleibt

Stand: 26.10.2026. POS wird als Entwicklungsexperiment archiviert. WCWV ist wieder
das aktive Projekt. Die dortige Technik wird selektiv und nur für einen konkreten
nächsten Versuch übernommen; es gibt keinen automatischen Merge der beiden Pipelines.

## Lesbare Archivkopie

Nach Wiederherstellung aus dem privaten Übergabearchiv liegen POS-Dateien unter
`archive/prose-or-structure/`, darunter `src/`, `tests/`, `resources/`, `docs/` und
`data/`. Ein Git-Bundle erhält zusätzlich den vollständigen POS-Verlauf. Das Archiv
ist auch ohne Fortbestand des bisherigen POS-GitHub-Repositories nutzbar.

## Nützliche Ergebnisse

| Material im POS-Archiv | Nutzen und Grenze |
|---|---|
| `resources/claim_profile.md`, Schema und Codebook | Profil 0.1 trennt Aussage, sechs Kontextaspekte, Herkunft und abgeleitete Prüfaufgabe. Vorläufiges Entwicklungsformat, keine validierte Taxonomie. |
| `resources/annotation_protocol.md` | Getrennte Code-/Reportreferenzen, semantische Zuordnung, vollständige/teilweise/fehlende Abdeckung, getrennte Fehlerzustände. |
| `resources/profile_development/` | JSPWiki, Jackson XML und Commons Configuration mit Codeankern und Grenzfällen. KI-assistierte Beispiele, keine unabhängige Referenz. |
| `docs/RELATED_WORK.md`, `resources/references.bib` | Vorbereitete Literaturabgrenzung; keine vollständige Recherche oder bestätigte Neuheit. |
| `docs/projektstand.tex` und PDF | Ausführliche Erklärung mit echten ZIP-Beispielen; historischer Stand 06.10.2026, kein aktueller Arbeitsauftrag. |
| `src/04_generate_claims.py` | Technische D-Route und Revision; nur bei Bedarf später gezielt übernehmen. |
| `src/06_run_pilot.py` | Budgetierter Runner, Originalrequests, Rohantworten, Herkunft und Fehlererhalt. |
| `src/extraction_baselines.py`, `resources/baselines/` | Satzaufteilung und dokumentierte VeriScore-basierte Extraktion; keine VeriScore-Wahrheitsprüfung. |
| `data/pilot/live-001/` | Originalausgaben aller Pilotbedingungen, Ressourcen-Snapshots und Budgetjournal. |
| `data/annotations/pilot-001/` | Zehn neutrale Codepakete mit leeren Referenz-Arbeitsblättern; noch keine menschlichen Urteile. |

## Technisch durchgeführter Pilot

Fünf Fälle aus zwei Familien: VUL4J-15/64 (XXE) und VUL4J-41/43/76
(Pfadverarbeitung). Beide Varianten, je zwei Wiederholungen; zehn Codekontexte.
Modell war gpt-5.4-mini-2026-03-17 mit reasoning_effort=none. 82 Aufgaben,
76 formal erfolgreich, sechs ungültige Ausgaben, 122 API-Aufrufe ohne Retry.
Geschätzte API-Kosten rund 1,09 USD; genehmigte Obergrenze war einmalig 10 USD.
Der technische Bericht und seine Fehlerliste bleiben unverändert im Archiv.

P und D sahen pro Kernpaar identische Codebytes. Reportextraktion sah nur den
Report; D war vom Reporterfolg unabhängig. Zusatzversuche: D-Revision, mit/ohne
Kontextfelder sowie Satz-/VeriScore-Baselines auf einer Teilmenge. Daraus folgen
keine Qualitäts-, Wahrheits- oder Überlegenheitsaussagen. Menschliche Annotation fehlt.

## Was in WCWV noch nicht aktiv ist

WCWV verwendet weiterhin sein altes Schema mit schema_version=1 und drei Skripten.
POS verwendet profile_version=0.1, andere Felder und sieben Schritte. Die Formate
sind nicht austauschbar. POS-claims.jsonl nicht als WCWV-Schema-1-Dateien ausgeben.
Eine spätere Übernahme braucht expliziten Vergleich, kleine Änderungen und Tests.

Das XML-/YAML-Material im Archiv darf sofort als Entwicklungsreferenz gelesen
werden, ohne Code oder Schema zu migrieren. Entwicklung und alle bekannten
Pilotprojekte samt Varianten bleiben aus einer späteren unabhängigen Evaluation heraus.

## Historische WCWV-Evidenz ist jetzt ebenfalls gesichert

Anders als die frühere POS-Übernahme enthält das private Rechnerarchiv auch die
ursprünglichen WCWV-Decomposition-Rohdaten, die abgegebene Annotation samt Review
und die Java-PoV-Logs/Surefire-Berichte. Der alte POS-Hinweis „hier nicht vorhanden“
beschreibt den damaligen POS-Import und darf nicht als Verlust dieser Dateien
nach der Wiederherstellung missverstanden werden. Kein Java-Neulauf wurde durchgeführt.
