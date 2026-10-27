# Zielclaims für JSPWiki Jackson XML und Commons YAML

**KI-unterstützter Arbeitsentwurf vom 26.10.2026, erstellt mit Codex. Fachliches
Gegenlesen ausstehend.** Dies ist eine Entwicklungsreferenz, keine unabhängig
bestätigte Ground Truth. Die drei Fälle und ihre Varianten sind bekannte
Entwicklungsmaterialien und für einen späteren frischen Holdout ungeeignet.

## Herkunft und Geltungsbereich

SG und Codex haben den JSPWiki-Report bereits mit Vorwissen über Code, Fix und PoV
bearbeitet. Auch frühere XML-/YAML-Entwürfe und Falllabels sind bekannt. Die hier
formulierten Zielclaims sind deshalb weder verblindet noch unabhängig. Als
Codebelege dienen ausschließlich die unten bezeichneten Dateien. Fix, Advisory,
Datasetlabel und historische PoV-Ergebnisse belegen hier keine Proposition.

[sources.json](sources.json) fixiert Dateien, SHA-256-Werte, Revisionen und
Zeilenbereiche. Alle Zeilenangaben unten sind Originalzeilen. Für Jackson gilt:
Originalzeile = lokale Textzeile + 83. Die Hashes wurden lokal abgeglichen.

| Fall | Erlaubter Code und Originalstand | Ausgeschlossener Kontext |
|---|---|---|
| JSPWiki / VUL4J-18 | Fünf Dateien unter [code](jspwiki/code/), Vul4J-Commit `07ad7850a041876befb99847053e4b5e181597a5`; Pfade in sources.json | WikiEngine, Filterimplementationen, Ziel-JSPs und effektives Deployment fehlen. |
| Jackson XML / VUL4J-47 | [XmlFactory.java.txt](jackson-xml/code/XmlFactory.java.txt), nur Originalzeilen 84–144; Upstream-Commit `48759e9822db9d7cbdf69faf519836e4c92ab5b1` | Übrige Klasse, Provider, Abhängigkeiten, Aufrufer und XML-Eingaben fehlen. |
| Commons YAML / VUL4J-9 | [YAMLConfiguration.java](commons-yaml/code/YAMLConfiguration.java), vollständig, Zeilen 1–145; Upstream-Commit `342f3b3be52bbbb188ad2fe81bb19ad688012123` | SnakeYAML-Version/-Implementation, geerbte Methoden, Aufrufer und Deployment fehlen. |

Reportreferenz heißt: Welche Bedeutung behauptet der Text, auch wenn sie falsch
ist? Codereferenz heißt: Welche begrenzten Aussagen und offenen Fragen erlaubt
das Eingabepaket? Eine Frage ist kein positiver Schwachstellenclaim. Die Kennungen
unten sind Leseanker, keine neue Ontologie und keine Vorgabe für die Claimzahl.
Alle Codeaussagen beschreiben den sichtbaren Kontrollfluss bei Erreichen der
jeweiligen Stelle und regulärer Rückkehr vorheriger Aufrufe; sie garantieren
keinen erfolgreichen Lauf. Aussagen über fremde Methoden beschränken sich auf
sichtbare Aufrufe, solange deren Implementationen fehlen.

## JSPWiki Reportreferenz

Quelle: [Finding](jspwiki/report.jsonl), ID
`0721c0a0-bba7-48c1-a63c-da196a69d97c:F001`.
Die [Originalabgabe von SG mit zwölf Claims](jspwiki/manual/manual_annotation_submitted_001.md)
und die [mit Codex überarbeitete Fassung mit 13 Claims](jspwiki/manual/manual_annotation_001.md)
sind getrennt erhalten. Die 13 historischen Claims sind eine assistierte
Reportzerlegung, keine 13 bestätigten Codewahrheiten.
Die folgende Arbeitsfassung hält deren Inhaltszuordnung nachvollziehbar.

### Unveränderte Quellpassagen

**T** (`title`):

> Path Traversal via PathInfo in WikiServlet

**S1** (`report`):

> In WikiServlet.java line 89, the method DefaultURLConstructor.parsePageFromURL is used to extract the page name from the request's pathInfo without sufficient validation.

**S2** (`report`):

> This value is then used in line 97-98 to construct a forward request dispatcher by concatenating it directly into the URL without sanitization.

**S3** (`report`):

> An attacker could craft a request with pathInfo containing directory traversal sequences (e.g., '../../etc/passwd') to potentially access unauthorized resources or bypass intended access controls.

**S4** (`report`):

> Although the DefaultURLConstructor.parsePageFromURL method (lines 245-268) only removes a leading slash and does not decode or validate the path further, the lack of additional checks in the servlet allows malicious path sequences to be forwarded to internal JSPs, potentially leading to information disclosure or further exploitation depending on the target JSP's handling of the 'page' parameter.

### Zielbedeutungen des Reports

Diese Propositionen geben die Behauptungen des Reports wieder. Ihre Aufnahme
bestätigt keine Wahrheit. Bei S2 wird der Wertbezug ausschließlich aus S1 aufgelöst.

| ID / historische ID | Proposition des Reports | Quelle und Bedeutungsgrenze |
|---|---|---|
| J-R01 / C01 | In WikiServlet besteht eine Path-Traversal-Schwachstelle über PathInfo. | T; kategorisches Label, keine bestätigte Ausnutzbarkeit. |
| J-R02 / C03 | In WikiServlet.java Zeile 89 wird DefaultURLConstructor.parsePageFromURL zur Extraktion des Seitennamens verwendet. | S1; benannte Operation und behauptete Position. |
| J-R03 / C04 | DefaultURLConstructor.parsePageFromURL extrahiert den Seitennamen aus request.pathInfo. | S1; Herkunft des Werts. |
| J-R04 / C05 | DefaultURLConstructor.parsePageFromURL extrahiert den Seitennamen aus request.pathInfo ohne ausreichende Validierung. | S1; „ohne ausreichende“ bedeutet nicht „ohne jede Prüfung“. |
| J-R05 / C07 | Der aus request.pathInfo extrahierte Seitenname wird in WikiServlet.java Zeilen 97–98 direkt mit der URL verkettet, um einen Forward-Request-Dispatcher zu erzeugen. | S1 + S2; „direkt“ bleibt die Reportbehauptung, keine Reparatur aus Codewissen. |
| J-R06 / C08 | Der aus request.pathInfo extrahierte Seitenname wird beim Erzeugen dieses Forward-Request-Dispatchers ohne Sanitization mit der URL verkettet. | S1 + S2; Negation nur für diese Verwendung; Sanitization-Begriff unbestimmt. |
| J-R07 / C09a | Ein Angreifer könnte einen Request konstruieren, dessen pathInfo Traversalsequenzen wie '../../etc/passwd' enthält. | S3; möglicher Angriffsschritt, Payload nur Beispiel. Anmeldung/Rechte nicht genannt. |
| J-R08 / C09b | Mit einem Request, dessen pathInfo solche Traversalsequenzen enthält, könnte ein Angreifer möglicherweise auf nicht autorisierte Ressourcen zugreifen oder vorgesehene Zugriffskontrollen umgehen. | S3; Möglichkeit und Alternative erhalten; weder beliebige Dateien noch anonymer Zugriff behauptet. |
| J-R09 / C11a | DefaultURLConstructor.parsePageFromURL (behauptete Zeilen 245–268) entfernt nur einen führenden Slash. | S4; „nur“ unverändert, aber mehrdeutig: einzige Stringtransformation oder gesamtes Verhalten? |
| J-R10 / C11b | DefaultURLConstructor.parsePageFromURL dekodiert den Pfad nicht weiter. | S4; lokale Negation; keine Behauptung über vorherige Containerdekodierung oder Schutzwirkung von Dekodieren. |
| J-R11 / C11c | DefaultURLConstructor.parsePageFromURL validiert den Pfad nicht weiter. | S4; nicht auf alle Komponenten erweitern. |
| J-R12 / C11d | Das Fehlen zusätzlicher Prüfungen im Servlet ermöglicht die Weiterleitung bösartiger Pfadsequenzen an interne JSPs. | S4; behauptete Ursache und Weiterleitung bleiben verbunden; „zusätzliche“ erhalten. |
| J-R13 / C12 | Die Weiterleitung bösartiger Pfadsequenzen an interne JSPs könnte zu Informationspreisgabe oder weiterer Ausnutzung führen, abhängig von der Verarbeitung des page-Parameters durch die Ziel-JSP. | S4; mögliche alternative Folgen, explizite Ziel-JSP-Bedingung. Rechte und konkrete Folgeausnutzung fehlen. |

T und S1–S4 sind damit inhaltlich adressiert; keine Empfehlung oder weitere Passage
liegt vor. Die Tabelle übernimmt die historische Unterteilung zur Nachverfolgbarkeit,
nicht als optimale Zielanzahl. J-R02/03/04 können etwa gemeinsam ausgedrückt werden,
wenn Aufrufposition, Datenherkunft und eingeschränkte Validierungsbehauptung erhalten
bleiben. „Nicht ausreichend validiert“ ist ohne benannte Operation zu klein.

Für den Titel sind zwei Lesarten zum Gegenlesen offen: eigenes kategorisches Label
wie oben oder integriertes Label eines größeren Claims. Ein Weglassen ist nur dann
gleichwertig, wenn keine zusätzliche Bedeutungsstärke verloren geht. Der historische
Review akzeptierte den Titel als Zusammenfassung; als eigene Aussage ist seine
kategorische Stärke zu beachten. Welche Lesart die Zielreferenz verwendet, bleibt
beim Gegenlesen zu entscheiden.

## JSPWiki Codereferenz

Die fünf vollständigen Eingabedateien liegen unter [jspwiki/code](jspwiki/code/).
`sources.json` erhält die ursprünglichen Pfade über ihre fixierten Quell-URLs.

Der zentrale Originalausschnitt aus WikiServlet.java 89–100 lautet:

```java
        String pageName = DefaultURLConstructor.parsePageFromURL( req, m_engine.getContentEncoding() );

        log.info( "Request for page: " + pageName );
        if( pageName == null ) {
            pageName = m_engine.getFrontPage(); // FIXME: Add special pages as well
        }

        String jspPage = m_engine.getURLConstructor().getForwardPage( req );
        RequestDispatcher dispatcher = req.getRequestDispatcher( "/" + jspPage + "?page=" +
                                                                 m_engine.encodeName( pageName ) + "&" + req.getQueryString() );

        dispatcher.forward( req, res );
```

| ID | Codegestützter Zielclaim im begrenzten Scope | Codeanker und verbleibende Grenze |
|---|---|---|
| J-C01 | parsePageFromURL liest request.getPathInfo(); bei null oder Länge ≤ 1 liefert es null, sonst entfernt es einen vorhandenen führenden Slash und gibt den verbleibenden Wert zurück. Ohne führenden Slash bleibt der Wert unverändert. Ein Decode-Aufruf ist nur auskommentiert. | DefaultURLConstructor.java 245–268; beschreibt Guards und Transformation, keine Aussage über den Eingangswert vor dem Requestobjekt. |
| J-C02 | WikiServlet.doGet verwendet das Ergebnis von parsePageFromURL als pageName und ersetzt es bei null durch m_engine.getFrontPage(). | WikiServlet.java 89–94; die Herkunft ist nicht für jeden Pfad unverändert pathInfo. |
| J-C03 | WikiServlet.doGet verwendet das Ergebnis von m_engine.getURLConstructor().getForwardPage(req) als jspPage im Pfadanteil des Dispatcherarguments; pageName wird über m_engine.encodeName(pageName) nach '?page=' eingesetzt, danach folgen '&' und req.getQueryString(). Anschließend wird dispatcher.forward(req,res) aufgerufen. | WikiServlet.java 96–100; Pfad und Query getrennt. encodeName wird aufgerufen, seine Wirksamkeit ist unbekannt. Der Aufruf garantiert keine erfolgreiche Weiterleitung. |
| J-C04 | Die gezeigte Implementation DefaultURLConstructor.getForwardPage gibt request.getPathInfo() unmittelbar zurück. Falls die Engine diese Implementation verwendet, liefert sie diesen Wert als jspPage an den Servletaufruf. | DefaultURLConstructor.java 278–281 + WikiServlet.java 96–98; aktive Implementation und effektive Requestverarbeitung bleiben offen. |
| J-C05 | In parsePageFromURL 245–268 ist neben Null-/Längenprüfung und Slashentfernung keine explizite Zurückweisung von Traversalsequenzen enthalten; WikiServlet.doGet 88–100 enthält vor der Dispatcherkonstruktion keine eigene explizite Traversalprüfung von jspPage. | Lokale negative Aussage; keine Verneinung von Prüfungen in aufgerufenen Methoden, Filtern oder Container. Kein Urteil, dass vorhandene Behandlung insgesamt unzureichend ist. |

| Offene Frage | Benötigte zusätzliche Evidenz und Bedeutung |
|---|---|
| J-Q01: Welche URLConstructor-Implementation ist aktiv, und was tut encodeName? | WikiEngine und effektive Konfiguration fehlen. Die Auswahl in jspwiki.properties 438–439 ist auskommentiert; URLConstructor als Interface entscheidet die Laufzeitwahl nicht. |
| J-Q02: Welche Requests erreichen doGet und mit welchen Rechten? | web.xml 57–77 und 158–161 zeigt Filter-/Servletmappings, aber keine Filterimplementation. Authentisierung, Wrapper, vorherige Dekodierung und Deployment müssen geprüft werden. Keine anonyme Angreiferreichweite behaupten. |
| J-Q03: Welche Ziele/Wirkungen ergeben sich beim Forward? | Containerauflösung, Ziel-JSP-Verarbeitung, Zugriffskontrollen und Dienstprozessrechte fehlen. Für Ressourcen außerhalb erlaubter Bereiche braucht es sowohl Erreichbarkeit als auch passende Lese-/Zugriffsrechte. Die Dateisystempayload des Reports ist kein Beleg für Dateilektüre. |

### Bedeutungstreue ist von Codeunterstützung verschieden

| Reportbedeutung | Einordnung am Code, noch keine menschliche Bestätigung |
|---|---|
| J-R02/03: Aufruf und PathInfo-Herkunft | J-C01/02 stützen den Extraktionspfad; der Fallback begrenzt Aussagen über spätere Verwendung. |
| J-R05: „direkt in die URL“ | Die konkrete Lesart „pageName wird unverändert zum Dispatcherpfad“ widerspricht J-C03. Eine allgemeinere Lesart „fließt in die URL ein“ ist möglich, muss aber Encode-Aufruf, Fallback und Trennung von Pfad/Query berücksichtigen. Keine stille Textkorrektur in J-R05. |
| J-R04/06/11: ausreichende Validierung / Sanitization / keine weitere Validierung | Null-/Längenguards widerlegen nicht automatisch „unzureichend“. encodeName ist kein Beleg für ausreichende Sanitization. Die weite Behauptung fehlender Validierung braucht eine geklärte Lesart; lokal ist J-C05 enger. |
| J-R09/10: „nur Slash“ / kein weiteres Dekodieren | Kein aktiver Decode-Aufruf in dieser Methode. Die Lesart „keine weiteren Operationen“ übersieht Guards und Rückgabezweige; die Lesart „einzige Stringtransformation“ passt zum Ausschnitt. |
| J-R01/07/08/12/13: Label, Angriff, Kausalität und Folgen | Mit dem Paket nicht abschließend entscheidbar: J-Q01–03. Reporttreue eines Claims bestätigt keine dieser Wirkungen. |

### Alternative Ebenen am JSPWiki-Beispiel

Eine feinere Variante von J-C03 trennt (a) Herkunft/Verwendung von jspPage,
(b) encodeName(pageName) im Queryparameter samt angehängter Query und (c) Forward-Aufruf.
Jeder Satz muss seine Variable und Verwendung nennen. Diese Variante und J-C03
können dieselben Inhalte abdecken; mehrfach genannte Codestellen zählen nicht doppelt.

Eine mittlere Zusammenfassung lautet: „Falls die Engine die gezeigte
DefaultURLConstructor.getForwardPage-Implementation verwendet, setzt doGet deren
PathInfo-Rückgabe in den Dispatcherpfad und den über encodeName behandelten
Seitennamen separat in den Queryparameter page ein.“ Sie verbindet J-C02–04,
ersetzt aber keine Detailabdeckung des Null-Fallbacks oder der restlichen Query.

Die höhere Angriffsaussage „Ein Angreifer kann unautorisiert Ressourcen lesen“
ist durch diese Zusammenfassung nicht bewiesen. Dafür müssen J-Q01–03 und ein
konkreter unerlaubter Zugriff geklärt sein. Ein Link auf J-C01–05 genügt nicht.
Als Reportclaim bleibt die schwächere Möglichkeitsaussage J-R08/13 erhalten.

## Jackson XML Codereferenz

Eigenständiges Thema: bedingte Parserkonfiguration und externe Factories. Das
vorhandene Entwicklungsbeispiel enthält ausgewählte Codeclaims, keinen vollständigen
XML-Report als Grundlage einer Reportreferenz. Hier wird kein Report erfunden.

Originalzeilen 112–123 (lokale Zeilen 29–40):

```java
        if (xmlIn == null) {
            xmlIn = XMLInputFactory.newInstance();
            // as per [dataformat-xml#190], disable external entity expansion by default
            xmlIn.setProperty(XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES, Boolean.FALSE);
        }
        if (xmlOut == null) {
            xmlOut = XMLOutputFactory.newInstance();
        }
        _initFactories(xmlIn, xmlOut);
        _xmlInputFactory = xmlIn;
        _xmlOutputFactory = xmlOut;
    }
```

| ID | Codegestützter Zielclaim im begrenzten Scope | Originalanker und Grenze |
|---|---|---|
| X-C01 | Wenn xmlIn null ist, erzeugt der gezeigte Hauptkonstruktor über XMLInputFactory.newInstance() eine Factory und ruft auf dieser setProperty(IS_SUPPORTING_EXTERNAL_ENTITIES, Boolean.FALSE) auf. | 104–116; bedingter Setter-Aufruf, keine Garantie über alle Provider oder nachfolgende Konfiguration. |
| X-C02 | Bei nicht-null übergebenem xmlIn überspringt der Hauptkonstruktor diesen Entity-Property-Setter; er reicht xmlIn an _initFactories weiter und weist es anschließend _xmlInputFactory zu. | 104–123; nicht „die übergebene Factory ist unsicher“ oder „sie hat keinen Schutz“. |
| X-C03 | Die gezeigte _initFactories-Implementation setzt an xmlIn IS_COALESCING auf Boolean.TRUE und enthält keinen Setter für IS_SUPPORTING_EXTERNAL_ENTITIES oder SUPPORT_DTD. Auch im Hauptkonstruktor 104–123 ist kein SUPPORT_DTD-Setter enthalten. | 138–144 und 104–123; lokale Abwesenheit, kein effektiver Defaultwert. Die protected Methode kann außerhalb des Ausschnitts überschrieben sein. |
| X-C04 | Der gezeigte Kopierkonstruktor übernimmt _xmlInputFactory von src, ohne in seinem sichtbaren Körper die Entity- oder DTD-Property neu zu setzen. | 128–136; eigene Konstruktorroute, keine Aussage über frühere Konfiguration der kopierten Factory. |

| Offene Frage | Benötigte Evidenz |
|---|---|
| X-Q01: Welche effektiven Properties und XML-Auflösungen gelten? | Konkreter Provider und Version, Propertyunterstützung/-Semantik, Resolver, weitere Setter und mögliche _initFactories-Overrides fehlen. Nicht gesetztes SUPPORT_DTD bedeutet weder true noch false. |
| X-Q02: Erreicht angreiferkontrolliertes XML einen Parser dieser Factory, und könnte es geschützte Ressourcen erreichen? | Parsererzeugung, Aufrufer, Eingabeherkunft/Authentisierung, DTD-/Entity-Verarbeitung, Netzwerk-/Dateizugriff und Rechte des Dienstprozesses fehlen. Factoryübergabe durch einen Aufrufer belegt keine Angreiferrechte. |

**Akzeptable Alternativen:** X-C01 darf Factory-Erzeugung und Setter getrennt
darstellen, wenn beide die Null-Bedingung und dieselbe Factory erhalten. X-C01/02
dürfen zusammen lauten: „Der Hauptkonstruktor setzt die Entity-Property selbst nur
im Null-Zweig; bei übergebener Factory überspringt er diesen Setter.“ Diese
Zusammenfassung deckt die lokale Konfigurationsasymmetrie ab, nicht automatisch
alle Detailoperationen oder X-C03/04.

**Unzulässige Verstärkungen:** „Jede Factory deaktiviert externe Entities“ ignoriert
den Nicht-null-Zweig und den Kopierkonstruktor. „DTD ist aktiviert“ verwechselt
fehlenden Setter mit effektivem Wert. „XXE ist ausgeschlossen“ bzw. „XXE liest
beliebige Dateien“ erfordern zusätzliche Evidenz aus X-Q01/02. Die Beziehungen
X-C01–04 → Konfigurationsasymmetrie → mögliche XXE-Wirkung sind Lesehilfen;
die zweite Stufe bleibt ohne jene Evidenz offen. Das Wort „deaktiviert“ sollte im
Zielclaim zunächst durch den belegten Setter-Aufruf präzisiert werden.

## Commons YAML Codereferenz

Eigenständiges Thema: Eingabeübergabe, Optionsvarianten und Grenzen nachgelagerter
Typprüfung/Fehlerbehandlung. Auch hier liegt im benannten Entwicklungsmaterial kein
vollständiger Report vor; die Referenz wird aus dem vorhandenen Code ausgearbeitet.

Originalzeilen 63–76 zeigen einen der vier Ladepfade:

```java
    @Override
    public void read(final Reader in) throws ConfigurationException
    {
        try
        {
            final Yaml yaml = new Yaml();
            final Map<String, Object> map = (Map) yaml.load(in);
            load(map);
        }
        catch (final Exception e)
        {
            rethrowException(e);
        }
    }
```

| ID | Codegestützter Zielclaim im begrenzten Scope | Originalanker und Grenze |
|---|---|---|
| Y-C01 | read(Reader) und read(InputStream) ohne LoaderOptions erzeugen jeweils new Yaml() und übergeben in an yaml.load(in). Bei regulärer Rückkehr und erfolgreichem Map-Cast übergeben sie das Ergebnis an load(map). | 63–76 und 115–128; zwei ausdrücklich benannte Overloads. Die Quelle von in ist unbekannt. |
| Y-C02 | read(Reader, LoaderOptions) und read(InputStream, LoaderOptions) erzeugen jeweils new Yaml(options), übergeben in an yaml.load(in) und bei regulärer Rückkehr und erfolgreichem Map-Cast das Ergebnis an load(map). | 78–91 und 130–143; kein Schluss auf bestimmte Optionswerte oder ihre Sicherheit. |
| Y-C03 | In diesen vier read-Methodenkörpern steht vor yaml.load(in) keine explizite Prüfung der Eingabe auf erlaubte YAML-Tags oder Typen. | 63–91 und 115–143; lokale Abwesenheit. Prüfungen in Yaml-Konstruktoren, yaml.load oder Aufrufern sind damit nicht ausgeschlossen. |
| Y-C04 | Der Map-Cast erfolgt nach dem Aufruf yaml.load(in); die vier Methoden fangen Exception aus ihrem try-Block und rufen rethrowException(e) auf. | Dieselben vier Methoden; weder der nachgelagerte Cast noch der Catch belegt, dass yaml.load ohne Nebenwirkungen ist. Verhalten der geerbten Hilfsmethoden fehlt. |

| Offene Frage | Benötigte Evidenz |
|---|---|
| Y-Q01: Welche Typen, Tags und Nebenwirkungen erlaubt das tatsächliche yaml.load? | SnakeYAML-Version und Implementation, Standardkonstruktor, LoaderOptions-Werte und ihre Semantik fehlen. new Yaml() allein belegt keine gefährliche Objektkonstruktion. |
| Y-Q02: Welche Eingaben erreicht ein Angreifer mit welchen Rechten? | Aufrufer, Vertrauensgrenzen, benötigte Anmeldung/Schreibrechte und Deployment fehlen; ein Reader/InputStream ist kein Beleg für externen oder anonymen Zugriff. Für Codeausführung wären zusätzlich ein konkreter Ausführungspfad und Dienstprozessrechte erforderlich. |
| Y-Q03: Wie wirken Map-Cast, load(map) und rethrowException im Gesamtablauf? | Geerbte Implementationen und Verhalten bei Fehlern fehlen. Eine Ausnahme nach yaml.load belegt weder Exploiterfolg noch Rücknahme vorheriger Nebenwirkungen. |

**Akzeptable Alternativen:** Y-C01 darf je Eingabetyp aufgeteilt werden. Ebenso
darf der gesamte Datenfluss pro Overload als ein Claim stehen, wenn Konstruktorwahl,
yaml.load, Map-Cast und nachgelagerter Aufruf erhalten bleiben. Die zwei gleichartigen
Overloads zählen nicht mehrfach für denselben Inhalt; wenn eine Aussage ausdrücklich
beide Eingabetypen umfasst, muss die Zuordnung auch beide prüfen. Ein Claim nur über
Reader deckt InputStream nicht automatisch mit ab.

Eine mittlere Aussage kann lauten: „Alle vier gezeigten read-Overloads übergeben
ihre Eingabe an eine lokal erzeugte Yaml-Instanz; die beiden Options-Overloads
verwenden new Yaml(options), die anderen new Yaml().“ Dies ist eine belegbare
Kontrollflusszusammenfassung, aber keine vollständige Abdeckung von Y-C01–04.

Die höhere Aussage „Ein Angreifer könnte mittels YAML Code ausführen“ bleibt eine
zu untersuchende Hypothese mit Y-Q01/02, kein positiver Zielclaim. Sie wird weder
durch Links auf Y-C01–04 noch durch ein bekanntes Datasetlabel bewiesen.
Umgekehrt beweisen Map-Cast oder Catch keine sichere Ablehnung vor dem Laden.

## Vorläufige Granularitätsregeln aus den drei Beispielen

1. Eine Einheit hat einen benannten Gegenstand, eine beurteilbare Aussage und
   ihren notwendigen Scope. „false“, „ohne Validierung“ oder eine Zeilennummer
   allein reichen nicht. Triviale Imports/Zuweisungen werden nur aufgenommen,
   wenn sie einen sicherheitsrelevanten Unterschied sichtbar machen.
2. Trennen lohnt sich bei unabhängig beurteilbaren Inhalten: JSPWiki-Pfad/Query,
   Jackson-Null-/Nicht-null-Zweig, YAML-Optionsvarianten. Nicht automatisch jede
   Operation aufteilen. Die geeignete Granularität hängt von der Bewertungsfrage ab.
3. Bedingungen gehören in jede betroffene Proposition: xmlIn == null, aktiver
   URLConstructor, Ziel-JSP-Verarbeitung. Verweise ersetzen diese Bedingungen nicht.
   Eine offene Rechtebedingung wird nicht durch Ergänzen eines Akteurs zur Tatsache.
4. Negation lokal begrenzen; „keine explizite Prüfung in diesen Methoden“ ist
   schwächer als „kein Schutz im System“. Nicht gesetzt, explizit false und unbekannt
   sind verschiedene Aussagen. „Könnte A oder B“ bleibt modal und alternativ.
5. Andere Formulierungen und Ebenen sind zulässig, wenn der relevante Inhalt mit
   Bedingungen rekonstruierbar bleibt. Eine grobe Zusammenfassung kann korrekt sein
   und dennoch Details nur teilweise abdecken. Wahrheit, Abdeckung und Granularität
   sind getrennte Urteile; keine reine Wortlaut- oder Claimzahlmetrik.
6. Mehrere Claims dürfen gemeinsam eine Zielbedeutung abdecken. Ihre gemeinsame
   Formulierung muss die Beziehung erhalten; insbesondere beweisen separate Fakten
   über Datenherkunft und Dispatcher noch keinen unerlaubten Zugriff.
7. Höhere Claims brauchen eine eigene Begründung: Welche untergeordneten Aussagen
   tragen welchen Teil, welche Annahmen fehlen? Eine Hierarchie ist keine Ableitung.
   Offene Voraussetzungen bleiben offen und dürfen nicht als erfüllte Teilclaims
   ausgegeben werden. Ein zusätzlicher Modellclaim kann korrekt sein; separat prüfen,
   nicht automatisch als Fehler zählen oder die Referenz still anpassen.

Offene Fragen und alternative Ebenen bleiben zunächst in diesen Tabellen. Ein
festes Ausgabeformat ist erst anhand der fachlich gegengelesenen Beispiele festzulegen.

## Begründung der Darstellung

Explizite Claims machen bestimmte Unterschiede adressierbar. Bei JSPWiki lässt sich
die Reportbehauptung über den Dispatcher getrennt von der möglichen Wirkung
diskutieren; eine Korrektur am Datenfluss muss nicht unbemerkt das Wirkungsurteil
ändern. Bei Jackson kann ein Gegenleser gezielt die Null-Bedingung und den Unterschied
zwischen Setter und effektiver Konfiguration prüfen. Bei YAML lassen sich Aussagen
über beide Eingabetypen und Optionsvarianten vergleichen, ohne ähnliche Formulierungen
als identisch vorauszusetzen. Quellen und offene Voraussetzungen bleiben je Aussage
sichtbar. Über Revisionen kann man nachvollziehen, welche Bedeutung geändert wurde.

Für eine spätere gezielte Prüfung wäre etwa die Frage nach der aktiven
URLConstructor-Implementation enger als „ist JSPWiki verwundbar?“. Die Darstellung
benennt dabei eine Prüfaufgabe und fehlende Eingaben; sie liefert selbst weder die
Übersetzung in ein Werkzeug noch den Nachweis. Das ist eine Arbeitsmotivation,
kein gemessener Gewinn an Zeit, Erkennungsrate, Verlässlichkeit oder Nutzerverständnis.

Literaturansatz für diese Motivation:

- [DecompScore](https://aclanthology.org/2024.starsem-1.13/): Bewertung der Zerlegung.
- [VeriScore](https://aclanthology.org/2024.findings-emnlp.552/): verständliche Aussagen mit notwendigen Modifikatoren; Übertragbarkeit auf modale Security-Claims prüfen.
- [CAE](https://www.adelard.com/asce/cae/) und [SACM](https://www.omg.org/spec/SACM/2.2): Trennung von Aussage, Annahme und Evidenz.
- [Tam et al. 2024](https://aclanthology.org/2024.emnlp-industry.91/): Abgrenzung gegenüber reinen Formatvergleichen.

Diese Literaturzuordnung ist vor einer Publikation am Original nachzuprüfen; sie
belegt keine Neuheit oder Leistungsverbesserung. Der Untersuchungsgegenstand ist
die bedeutungstreue Erzeugung und Zerlegung fachlich sinnvoller Zielclaims im
begrenzten Codekontext.

## Fachliches Gegenlesen mit SG vorbereiten

Vorschlag für die nächste gemeinsame Sitzung, noch kein erhobenes menschliches Urteil:

1. SG liest zuerst die bezeichneten Codeausschnitte und Codeclaims, mit der dokumentierten
   Vorkenntnis. Je Aussage prüfen wir Bedeutung, Scope, notwendige Bedingungen und
   fachliche Relevanz. Offene Bibliotheks-/Deploymentfragen nicht erraten.
2. Anschließend J-R01–13 am unveränderten Report auf Treue prüfen. Den strittigen
   Titelstatus, „nur“, „direkt“ und „Sanitization“ ausdrücklich entscheiden; Änderungen
   am Reportziel nicht mit fachlichen Codekorrekturen vermischen.
3. Pro Fall eine feinere und eine mittlere Darstellung durchgehen: gleiche Bedeutung,
   nur teilweise Abdeckung oder unzulässige Verstärkung? Die drei höheren
   Angriffsaussagen anhand der fehlenden Evidenz abgrenzen.
4. SGs ursprüngliche Urteile vor einer gemeinsam formulierten Korrektur festhalten.
   Codex-Hilfe, Code/Fix/PoV-Vorwissen und bereits bekannte Outputs weiter ausweisen.
   SGs Gegenlesen wäre eine fachliche Kontrolle, keine unabhängige Doppelannotation.
   Ob und durch wen zusätzliches qualifiziertes Gegenlesen erfolgt, gemeinsam entscheiden.
5. Erst nach Klärung eine Zielreferenz mit Quellenhashes fixieren. Danach erzeugte
   Claims nach semantischer Abdeckung, Bedeutungsänderungen und Zusatzinhalten
   zuordnen; diese Fälle bleiben Entwicklungsfälle. Keine neue Studie oder API-Freigabe
   aus dem Gegenlesen ableiten.

| Prüfpunkt | Originalurteil SG | Begründung und Änderung | Offene Evidenz / Entscheidung |
|---|---|---|---|
| JSPWiki Reporttreue und Titelstatus | ausstehend | ausstehend | Lesarten von „direkt“, „nur“, Sanitization |
| JSPWiki Codeclaims und höhere Aussage | ausstehend | ausstehend | J-Q01–03 |
| Jackson Bedingungen und Konfigurationsscope | ausstehend | ausstehend | X-Q01/02, mögliche Overrides |
| YAML Overloads und Reihenfolge | ausstehend | ausstehend | Y-Q01–03 |
| Granularität und Nutzenbegründung | ausstehend | ausstehend | Welche Inhalte sind für das begrenzte Ziel nötig? |
