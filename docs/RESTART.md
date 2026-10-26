# Umzug und Neustart auf dem privaten Rechner

Stand: 26.10.2026. Dies ist die Einstiegsanleitung nach dem Rechnerwechsel.
**Aktives Projekt ist What Can We Verify (WCWV).** Die POS-Entwicklung bleibt
als Referenz erhalten; ihre Pipeline wird nicht automatisch in WCWV eingebaut.

## 1. Beide benötigten Repositories klonen

Git und Python 3.9 oder neuer installieren und bei GitHub mit dem Account anmelden,
der Zugriff auf das private Archiv hat. In einen neuen Arbeitsordner wechseln:

```bash
git clone https://github.com/sebi-gr/What-Can-We-Verify.git
git clone https://github.com/sebi-gr/wcwv-handover-20261026.git
```

WCWV enthält den aktiven Code und die aktuelle Planung. Das **private** zweite
Repository enthält das unveränderte Gesprächstranskript, die bisher ignorierten
Forschungsdaten, die POS-Quelldateien und Git-Bundles. Nur WCWV zu klonen stellt
die historischen Daten noch nicht wieder her. Zugangsdaten sind in keinem Archiv.

## 2. Archiv prüfen und Daten wiederherstellen

Vom gemeinsamen Elternordner aus ausführen (Windows alternativ mit `py -3`):

```bash
python wcwv-handover-20261026/restore.py --wcwv What-Can-We-Verify
```

Der Helfer prüft SHA-256-Hashes und ZIP-Pfade vor dem Entpacken und schreibt nur
in neue Zielordner. Er stellt diese Pfade her:

| Ziel unter WCWV | Inhalt |
|---|---|
| `data/` | Ursprüngliche WCWV-Eingaben, Reports, Decompositions, Annotationen und PoV-Evidenz |
| `archive/prose-or-structure/` | POS-Quelldateien am Übergabestand, einschließlich Dokumentation und Entwicklungsmaterial |
| `archive/prose-or-structure/data/` | POS-Pilot mit Requests/Rohantworten, Quellen und Annotationspaketen |

Wenn `data/` oder der POS-Zielordner schon existiert, stoppt der Helfer. Vorhandene
Daten nicht löschen, um den Befehl erneut auszuführen. Stattdessen zunächst den
Stand prüfen oder eine neue WCWV-Kopie verwenden. `--verify-only` prüft das Archiv
ohne Wiederherstellung. Bei Bedarf findet die nächste Session die Originalarchive
und Einzeldateihashes auch direkt im privaten Repository.

Die Portabelinstallationen von JDK/Maven, ihr Download-ZIP und der lokale
Maven-Abhängigkeitscache wurden bewusst nicht übernommen. URLs, Checksummen,
Befehle und Versionsinformationen bleiben erhalten. Die originalen Java-Quellen,
Build-/Testlogs, Surefire-Berichte und Ergebnisdateien sind gesichert. Python-
Caches und Zugangsdaten werden ebenfalls nicht wiederhergestellt.

## 3. Code und Teststand prüfen

```bash
cd What-Can-We-Verify
git status --short
python -X utf8 -m unittest -v
git diff --check
```

Die Tests sind offline und benötigen keinen API-Key oder Java. Ein Windows-
Symlink-Skip ist als solcher zu dokumentieren. Das ist keine Qualitätsbewertung
der Modelloutputs und kein erneuter Java-PoV. Aktuelle Zahlen stehen in HANDOFF.md.

## 4. Neue Codex-Session im WCWV-Ordner starten

In Codex **What-Can-We-Verify** als Projekt öffnen. Den Text aus
[NEXT_SESSION_PROMPT.md](NEXT_SESSION_PROMPT.md) als erste Nachricht verwenden.
Die Session soll zuerst AGENTS.md, HANDOFF.md, WORKPLAN.md und README.md lesen,
anschließend die fachliche Zusammenfassung und bei Bedarf das private Transkript.

Die privaten Gesprächsdateien bleiben im separaten Archiv. Nicht in ein öffentliches
Repository kopieren. Die öffentlichen Übergabedokumente enthalten nur die für die
Forschung nötigen Entscheidungen und Aufgaben.

## 5. Konfiguration erst für einen späteren genehmigten Modelllauf anlegen

Für die Referenzarbeit ist kein API-Key nötig. Bei späterem Bedarf `.env.example`
lokal nach `.env` kopieren und einen eigenen gültigen Key einsetzen. Alte Schlüssel
werden nicht übertragen. Keine alten `.env`-Dateien oder Browser-/Git-Anmeldedaten
aus dem Firmenrechner übernehmen. Die alte 10-USD-Freigabe galt nur dem abgeschlossenen
POS-Pilot. Kein neuer Modelllauf, Retry oder Modellwechsel ist damit freigegeben.
Die WCWV-Standalone-Skripte haben keinen monetären Schutz.

## 6. Fachlich weiterarbeiten

1. Begründung der Claim-Darstellung mit Literatur und konkreten Anwendungen ausarbeiten.
2. JSPWiki als Entwicklungsbeispiel wieder aufnehmen; Reportreferenz und Codereferenz unterscheiden.
3. Zwei weitere unterschiedliche Entwicklungsbeispiele vollständig von Hand bearbeiten.
4. Zielclaims, Kontextgrenzen und akzeptable Abstraktionsebenen fachlich gegenlesen lassen.
5. Vorhandene Modelloutputs semantisch zuordnen; erst danach weitere Generierung planen.

Der nächste Termin mit Andreas soll konkrete Zielbeispiele und begründete
Granularitätsregeln diskutieren, nicht eine neue Verifikationsplattform abnehmen.

## 7. Erst dann die alte lokale Umgebung entfernen

Vor dem Löschen dieses Rechners müssen die entfernten GitHub-Commits und das
private Archiv aus einem frischen Clone geprüft sein. Vor allem eine erfolgreiche
Wiederherstellung einschließlich Dateihashes muss vorliegen. Das Übergabemanifest
im privaten Archiv hält Umfang und bewusste Ausschlüsse fest.

Die POS-Arbeitskopie wird für die Weiterarbeit nicht benötigt. Selbst wenn auch
das POS-Repository auf GitHub später entfernt wird, enthält das private Archiv
seinen vollständigen Git-Verlauf als Bundle und einen direkt lesbaren Snapshot.
Die Löschung auf GitHub ist eine separate Entscheidung; diese Übergabe löscht
keines der Repositories. Auch die private Sicherung muss erhalten bleiben.

## Vollständige Git-Historie bei Bedarf rekonstruieren

Die Bundles enthalten zusätzlich lokale Branches und Tags, einschließlich der
noch nicht auf ihren bisherigen Remote-Branches vorhandenen WCWV-Commits.
Für eine gesonderte historische Kopie aus dem gemeinsamen Elternordner:

```bash
git clone --mirror wcwv-handover-20261026/bundles/wcwv.bundle wcwv-history.git
git clone --mirror wcwv-handover-20261026/bundles/pos.bundle pos-history.git
```

Diese historischen Kopien nicht über die aktive WCWV-Arbeitskopie schreiben.
