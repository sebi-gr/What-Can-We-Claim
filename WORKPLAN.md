# Arbeitsplan: Sicherheitsclaims begründen und erzeugen

Stand: 26.10.2026. Maßgeblicher Plan nach der Besprechung mit Andreas und der
Entscheidung, im ursprünglichen WCWV-Repository weiterzuarbeiten. Technischer
Stand: [HANDOFF.md](HANDOFF.md). Gesprächseinordnung: [RESEARCH_DIRECTION.md](docs/RESEARCH_DIRECTION.md).

## Ziel

Sicherheitsbehauptungen aus Code beziehungsweise LLM-Reports in nachvollziehbare,
eigenständig beurteilbare Claims überführen. Zunächst an begründeten Zielbeispielen
untersuchen, welche Aussagen und Bedingungen ein geeignetes Format erhalten muss.
Den Nutzen der Darstellung aus Anwendungen und Literatur motivieren; keine bereits
nachgewiesene Verbesserung einer kompletten Security-Prüfung behaupten.

## Reihenfolge und Abschlusskriterien

| Schritt | Stand | Abschlusskriterium |
|---|---|---|
| 0. Rechnerübergabe | Datenwiederherstellung geprüft; Abschlussnachweis im privaten Archiv | Beide Git-Verläufe, Rohdaten und Transkript entfernt gesichert; alle 6.608 Archivdateien aus GitHub-Clone mit SHA-256 wiederhergestellt. |
| 1. Nutzen begründen | Argumente vorhanden, auszuarbeiten | Kurze Begründung mit konkreten Verwendungen, Literaturbelegen und klaren Aussagegrenzen. |
| 2. Zielbeispiele manuell ausarbeiten | JSPWiki-Reportzerlegung und POS-Entwürfe vorhanden | Drei unterschiedliche Entwicklungsbeispiele mit Codeankern, Zielclaims, Bedingungen, offenen Fragen und alternativen Zerlegungen. |
| 3. Abstraktionsniveau festlegen | Offen | An Beispielen begründete Granularitätsregeln; höhere Aussagen nur mit notwendigen Zusatzbedingungen. Hierarchie nur bei konkretem Bedarf. |
| 4. Zielreferenz fachlich kontrollieren | Offen | Qualifizierte Person(en) prüfen Korrektheit/Sinnhaftigkeit; Originalurteile, Vorwissen und Abweichungen dokumentiert. |
| 5. Modelloutputs zuordnen | Technik/Outputs vorhanden, Bewertung offen | Semantische Abdeckung, Bedeutungserhalt, Zusatzclaims und technische Fehler getrennt. Zulässige andere Formulierungen/Abstraktionen berücksichtigt. |
| 6. Weitere Studie festlegen | Offen | Mit Andreas Fallauswahl, menschlichen Aufwand, Matching, Umfang und eingefrorenes Versuchsprotokoll abstimmen. |

## Unmittelbarer nächster Arbeitsschritt

Zuerst das vorhandene JSPWiki-Beispiel als KI-unterstützten Arbeitsentwurf aufbereiten:
Codekontext, historische Reportreferenz, davon getrennte codegestützte Zielclaims,
offene Voraussetzungen und akzeptable alternative Zerlegungen. Nicht die alten
13 Claims als Codewahrheit oder feste Zielanzahl behandeln. Danach das vorhandene
XML-/YAML-Entwicklungsmaterial aus dem POS-Archiv ergänzen. Keine neue Pipeline nötig.

Mit diesen drei Beispielen und einer kurzen Nutzenbegründung wieder zu Andreas
gehen. Bis dahin keine große Annotation aller Pilotbedingungen organisieren und
keine zusätzlichen Modellläufe starten.

## Bereits vorhandene Basis

- WCWV: fixierter JSPWiki-Kontext, Report, assistierte 13-Claim-Annotation,
  automatische Zerlegung und historische Java-PoV-Evidenz.
- POS-Archiv: gemeinsames Profil 0.1 mit Kontextfeldern, getrennte Referenzregeln,
  Entwicklungsbeispiele und Literaturabgrenzung, P/D-Pilot und Zusatzvergleiche.
- Annotationsvorlagen/Zuordnungsregeln vorhanden; keine unabhängigen Pilotreferenzen,
  keine fertige semantische Auswertung und keine bestätigten Qualitätsresultate.

## Regeln für die nächsten Referenzen und Vergleiche

- Code- und Reportreferenz getrennt halten. Reporttreue ist keine Wahrheitsprüfung.
- Identischen erlaubten Codekontext verwenden; Fix/PoV/Advisory/Labels nicht in
  Generierung oder als versteckte Codebelege übernehmen. Externes Vorwissen benennen.
- Bedingungen, Modalität, Negation, Rechte, Quantoren und Scope im Satz erhalten.
- Abdeckung nach Bedeutung, nicht Wortlaut oder Claimzahl; mehrere Claims dürfen
  gemeinsam eine Einheit abdecken. Duplikate nicht mehrfach zählen.
- Ein Zusatzclaim außerhalb der Referenz kann korrekt sein: gesondert überprüfen,
  nicht automatisch als falsch werten oder die Referenz still nachträglich anpassen.
- Neue Evaluationsreferenzen vor Einsicht in Modelloutputs erstellen. Bekannte
  Entwicklungs-/Pilotprojekte samt Varianten nicht als frischen Holdout verwenden.
- Fehlender Kontext, technischer Ausfall und inhaltlicher Widerspruch sind verschiedene
  Zustände. Ein fehlgeschlagener PoV widerlegt keine Schwachstelle.
- Aktives Schema nur ändern, wenn die Zielbeispiele es begründen. POS-Profil 0.1
  nicht still mit WCWV-Schema 1 vermischen. Alte Laufressourcen unverändert erhalten.

## Zurückgestellt und offene Entscheidungen

P/D bleibt ein möglicher Vergleich, sobald Zielniveau und Referenzen belastbar sind.
Kontextablation, VeriScore und D-Revision sind vorhandene Zusatzversuche, nicht alle
automatisch Pflicht für das nächste Paper. Ein allgemeines Wichtigkeitsranking,
CodeQL-/Solver-Integration, Agentenplattform, Nutzerstudie oder allgemeiner
Nutzennachweis einer vollständigen Verifikationspipeline ist derzeit nicht beauftragt.

Eine zweite Veröffentlichung und eine feste Hauptstudien-Fallzahl sind nicht beschlossen.
Automatisches Matching oder LLM-Bewertung muss gegen menschlich geprüfte Beispiele
validiert werden. Für neue Modellversuche fehlt eine neue Budgetfreigabe.
