Kopiervorlage: Für einen Fall zuerst nach `data/annotations/` kopieren. Das aktuelle
Arbeitsblatt ist in [README.md](../README.md#3-manuell-zerlegen) verlinkt.

# Manuelle Zerlegung — {{FINDING_ID}}

## Zuordnung

- Status: vorbereitet; noch keine menschliche Annotation.
- Vorbereitung: {{PREPARED_BY_DATE}}
- Finding-Datei (Pfad relativ zur Repo-Wurzel): `{{SOURCE_PATH}}`
- SHA-256 der Finding-Datei: `{{SOURCE_SHA256}}`
- Finding-ID: `{{FINDING_ID}}`
- Codebook: `resources/claim_codebook.md`
- SHA-256 der verwendeten Codebook-Datei: `{{CODEBOOK_SHA256}}`
- Annotator/in (Kürzel): **AUSFÜLLEN**
- Bearbeitet am: **AUSFÜLLEN**
- Vorwissen / Hilfsmittel: {{PRIOR_KNOWLEDGE}}
- Wahrheitsprüfung aller Claims: `not_evaluated` (nicht Teil dieses Durchgangs).

Das Original unten nicht bearbeiten. Die Claim-Blöcke und Abschlussfelder sind
dein Arbeitsbereich. Ein Claim ist eine Behauptung, nicht notwendigerweise ein Satz.
`{{...}}` kennzeichnet Metadaten, die beim Vorbereiten einer neuen Kopie ersetzt
werden. Fallbezogene Arbeitsblätter liegen unter dem ignorierten `data/annotations/`.

## Original (unverändert)

### T — title

```text
{{TITLE}}
```

### report

```text
{{REPORT}}
```

## Abdeckung

{{COVERAGE_TABLE}}

Nach dem Zerlegen jeder Passage alle zugehörigen Claim-IDs zuordnen. Nicht jede
Passage braucht einen eigenen Claim: Wiederholungen dürfen auf denselben verweisen.
Nicht erfasste Teile begründen; Satzkennungen sind keine vorgegebene Zerlegung.
Ein Satz darf mehrere Claims mit unterschiedlichen Familien belegen. Ein Titel,
der nur den Report zusammenfasst, braucht keinen zusätzlichen Claim.

## Claims — diesen Block je weiterer Aussage kopieren

### C01

- **Originalzitat(e):** AUSFÜLLEN — `title`/`report`, T/Satzkennung und exakter Text;
  bei Bedarf mehrere Zitate einschließlich Bezugssatz.
- **Proposition:** AUSFÜLLEN — eine eigenständig verständliche Behauptung. Deutsch
  oder Englisch möglich; Fachbezeichner und behauptete Codepositionen erhalten.
- **Familie und Begründung:** AUSFÜLLEN — siehe Codebook; bei
  `exploitability_impact` zusätzlich Untertyp.
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** AUSFÜLLEN — im
  Original behauptete Akteure, Voraussetzungen und Einschränkungen; „nicht genannt“
  ist erlaubt. Diese Einschränkungen müssen auch in der Proposition erhalten bleiben.
- **Benötigter Kontext:** AUSFÜLLEN — andere Claim-IDs mit Erklärung oder „keiner“;
  ungelöste Bezüge ausdrücklich markieren.

## Grenzfälle / Vorschläge für das Codebook

| Passage oder Claim | Problem | Entscheidung oder offener Vorschlag | Begründung |
|---|---|---|---|
| AUSFÜLLEN | | | |

Wenn keine Grenzfälle auftreten, ausdrücklich „keine“ eintragen. Codefehler oder
Wahrheitsvermutungen nicht zur Korrektur der extrahierten Aussage verwenden.

## Abschluss durch den Menschen

- [ ] Titel und alle Reportsätze im Abdeckungscheck zugeordnet oder begründet ausgeschlossen.
- [ ] Jede Proposition hat exakte Originalzitate; aufgelöste Bezüge sind im Finding belegt.
- [ ] Negation, Modalität, Bedingungen, Alternativen und Geltungsbereich sind erhalten.
- [ ] Codepositionen oder Behauptungen wurden nicht mit Wissen aus Code/Fix/PoV korrigiert.
- [ ] Codebook-Grenzfälle und verwendete Hilfsmittel sind dokumentiert.
- Ergebnis des Durchgangs: **offen** — nach Bearbeitung kurz festhalten, ob noch
  Entscheidungen nötig sind. Keine Aussage über die Wahrheit der Claims ableiten.
