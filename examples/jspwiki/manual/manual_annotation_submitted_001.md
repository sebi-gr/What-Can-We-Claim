# Manuelle Zerlegung — {{FINDING_ID}}

## Zuordnung

- Status: vorbereitet; noch keine menschliche Annotation.
- Vorbereitung: {{PREPARED_BY_DATE}}
- Finding-Datei (Pfad relativ zur Repo-Wurzel): `{{SOURCE_PATH}}`
- SHA-256 der Finding-Datei: `{{SOURCE_SHA256}}`
- Finding-ID: `{{FINDING_ID}}`
- Codebook: `resources/claim_codebook_v0_1.md`
- SHA-256 der verwendeten Codebook-Datei: `{{CODEBOOK_SHA256}}`
- Annotator/in (Kürzel): **SG**
- Bearbeitet am: **24.09.2026**
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

## Claims — diesen Block je weiterer Aussage kopieren

### C01

- **Originalzitat(e):** Path Traversal via PathInfo in WikiServlet
  
- **Proposition:** Path Traversal Schwachstelle in WikiServlet Anwendung/Funktion vorhanden

- **Familie und Begründung:** `location`
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** keine

### C02

- **Originalzitat(e):** Path Traversal via PathInfo in WikiServlet
  
- **Proposition:** Path Traversal Schwachstelle über PathInfo Parameter ausnutzbar

- **Familie und Begründung:** `data_flow`
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** keine

### C03

- **Originalzitat(e):** In WikiServlet.java line 89, the method DefaultURLConstructor.parsePageFromURL is used to extract the page name from the request's pathInfo without sufficient validation.
  
- **Proposition:** Die Schwachstelle befindet sich in WikiServlet.java Zeile 89

- **Familie und Begründung:** `location`
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** keine

### C04

- **Originalzitat(e):** In WikiServlet.java line 89, the method DefaultURLConstructor.parsePageFromURL is used to extract the page name from the request's pathInfo without sufficient validation.
  
- **Proposition:** DefaultURLConstructor.parsePageFromURL wird vewendet um den Namen der Seite aus pathInfo des requests zu extrahieren

- **Familie und Begründung:** `data_flow`
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** keine

### C05

- **Originalzitat(e):** In WikiServlet.java line 89, the method DefaultURLConstructor.parsePageFromURL is used to extract the page name from the request's pathInfo without sufficient validation.
  
- **Proposition:** Without sufficient validation

- **Familie und Begründung:** `protection_precondition`
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** keine

### C06

- **Originalzitat(e):** This value is then used in line 97-98 to construct a forward request dispatcher by concatenating it directly into the URL without sanitization.
  
- **Proposition:** This value is then used in line 97-98

- **Familie und Begründung:** `location`
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** keine

### C07

- **Originalzitat(e):** This value is then used in line 97-98 to construct a forward request dispatcher by concatenating it directly into the URL without sanitization.
  
- **Proposition:** to construct a forward request dispatcher by concatenating it directly into the URL

- **Familie und Begründung:** `data_flow`
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** keine

### C08

- **Originalzitat(e):** This value is then used in line 97-98 to construct a forward request dispatcher by concatenating it directly into the URL without sanitization.
  
- **Proposition:** without sanitization

- **Familie und Begründung:** `protection_precondition`
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** keine

### C09

- **Originalzitat(e):** An attacker could craft a request with pathInfo containing directory traversal sequences (e.g., '../../etc/passwd') to potentially access unauthorized resources or bypass intended access controls.
  
- **Proposition:** An attacker could craft a request with pathInfo containing directory traversal sequences (e.g., '../../etc/passwd') to potentially access unauthorized resources or bypass intended access controls.

- **Familie und Begründung:** `exploitability_impact`
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** could, potentially

### C10

- **Originalzitat(e):** Although the DefaultURLConstructor.parsePageFromURL method (lines 245-268) only removes a leading slash and does not decode or validate the path further, the lack of additional checks in the servlet allows malicious path sequences to be forwarded to internal JSPs, potentially leading to information disclosure or further exploitation depending on the target JSP's handling of the 'page' parameter.
  
- **Proposition:** (lines 245-268)

- **Familie und Begründung:** `location`
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** keine

### C11

- **Originalzitat(e):** Although the DefaultURLConstructor.parsePageFromURL method (lines 245-268) only removes a leading slash and does not decode or validate the path further, the lack of additional checks in the servlet allows malicious path sequences to be forwarded to internal JSPs, potentially leading to information disclosure or further exploitation depending on the target JSP's handling of the 'page' parameter.
  
- **Proposition:** removes a leading slash and does not decode or validate the path further, the lack of additional checks in the servlet in the servlet allows malicious path sequences to be forwarded to internal JSPs,

- **Familie und Begründung:** `protection_precondition`
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** keine

### C12

- **Originalzitat(e):** Although the DefaultURLConstructor.parsePageFromURL method (lines 245-268) only removes a leading slash and does not decode or validate the path further, the lack of additional checks in the servlet allows malicious path sequences to be forwarded to internal JSPs, potentially leading to information disclosure or further exploitation depending on the target JSP's handling of the 'page' parameter.
  
- **Proposition:** potentially leading to information disclosure or further exploitation

- **Familie und Begründung:** `exploitability_impact`
- **Unsicherheit / Negation / Bedingungen / Geltungsbereich:** potentially, depending on the target JSP's handling of the 'page' parameter.

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
- [ ] Extraktionstreue und Typisierung wurden getrennt geprüft; offene Fälle sind sichtbar.
- [ ] Codebook-Grenzfälle und verwendete Hilfsmittel sind dokumentiert.
- Ergebnis des Durchgangs: **offen** — nach Bearbeitung kurz festhalten, ob noch
  Entscheidungen nötig sind. Keine Aussage über die Wahrheit der Claims ableiten.
