"""Build a detailed German personal briefing from preserved experiment evidence."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.platypus import CondPageBreak, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
CASES = ("jspwiki", "jackson-xml", "commons-yaml")
NAMES = {"jspwiki": "JSPWiki", "jackson-xml": "Jackson XML", "commons-yaml": "Commons YAML"}
NAVY, TEAL = colors.HexColor("#17324D"), colors.HexColor("#087F8C")
GRAY, PALE = colors.HexColor("#536373"), colors.HexColor("#EDF5F7")
WIDTH = A4[0] - 36 * mm


# Read required JSON; malformed or missing inputs stop the report before authoring.
def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


# Reject empty author judgments instead of inventing or automatically evaluating them.
def require_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Missing review text: " + field)
    return value


# Load complete run evidence and check every reviewed ID, coverage and support label.
# Frozen run baselines are authoritative; review is explicitly AI-assisted, not human.
def load_data(run_dir):
    run, review = read_json(run_dir / "run.json"), read_json(run_dir / "review.json")
    references = read_json(ROOT / "resources/references.json")
    if run.get("status") not in ("completed", "completed_with_invalid_outputs") or len(run.get("tasks", [])) != 9:
        raise ValueError("Report requires the completed nine-request experiment")
    if any(t.get("status") not in ("completed", "invalid_output") for t in run["tasks"]):
        raise ValueError("A generation task has no completed response")
    require_text(review.get("authorship"), "authorship")
    if review.get("human_validation") != "pending" or not review.get("criteria"):
        raise ValueError("Explicit AI-review criteria and human_validation=pending are required")
    rows = {r["case"]: r for r in review.get("cases", [])}
    if set(rows) != set(CASES) or len(review["cases"]) != 3:
        raise ValueError("Review must cover each of the three cases exactly once")
    data = {}
    for case in CASES:
        directory, row = run_dir / case, rows[case]
        baseline_path = directory / "baseline.json"
        if hashlib.sha256(baseline_path.read_bytes()).hexdigest() != run["baseline_hashes"][case]:
            raise ValueError("Frozen baseline hash mismatch: " + case)
        claims = {"baseline": read_json(baseline_path)["claims"], "prose": read_json(directory / "prose.json")["claims"]}
        envelope = read_json(directory / "code_claims.json")
        formal = envelope["status"]
        if formal == "completed":
            claims["direct"] = read_json(directory / "direct.json")["claims"]
        elif formal == "invalid_output" and not (directory / "direct.json").exists():
            # Decode the preserved raw answer without repairing or accepting evidence.
            response = envelope["response"]
            if response.get("status") != "completed":
                raise ValueError("Rejected direct answer has no complete raw text")
            raw = "".join(c["text"] for item in response["output"] if item["type"] == "message" for c in item["content"] if c["type"] == "output_text")
            claims["direct"] = json.loads(raw)["claims"]
        else:
            raise ValueError("Inconsistent direct artifact status: " + case)
        if not (directory / "report.txt").read_text(encoding="utf-8").strip():
            raise ValueError("Missing generated prose report: " + case)
        indexed = {route: {c["id"]: c for c in values} for route, values in claims.items()}
        if any(len(indexed[r]) != len(claims[r]) for r in claims):
            raise ValueError("Duplicate claim ID: " + case)
        assessed = row.get("baseline_assessment", [])
        if {r["baseline_id"] for r in assessed} != set(indexed["baseline"]) or len(assessed) != len(claims["baseline"]):
            raise ValueError("Every baseline claim needs one authored assessment: " + case)
        for item in assessed:
            for route in ("direct", "prose"):
                judgment = item[route]
                if judgment["coverage"] not in ("full", "partial", "missing"):
                    raise ValueError("Invalid coverage label")
                if any(i not in indexed[route] for i in judgment["ids"]):
                    raise ValueError("Assessment cites an unknown generated ID")
                if bool(judgment["ids"]) != (judgment["coverage"] != "missing"):
                    raise ValueError("Coverage label and matched IDs disagree")
                require_text(judgment.get("reason"), case + " coverage reason")
        for route in ("direct", "prose"):
            judgments = row["generated_claim_assessment"][route]
            if {j["id"] for j in judgments} != set(indexed[route]) or len(judgments) != len(claims[route]):
                raise ValueError("Every generated claim needs an authored assessment")
            for judgment in judgments:
                if judgment["code_support"] not in ("supported", "inconclusive", "contradicted", "mixed"):
                    raise ValueError("Invalid code-support label")
                if judgment["granularity"] not in ("acceptable", "too_broad", "fragment"):
                    raise ValueError("Invalid granularity label")
                if route == "prose" and judgment.get("report_faithful") not in ("yes", "partial", "no"):
                    raise ValueError("Missing prose report-faithfulness judgment")
                require_text(judgment.get("reason"), "generated-claim reason")
        example = row["example"]
        for route, key in (("baseline", "baseline_id"), ("direct", "direct_id"), ("prose", "prose_id")):
            if example.get(key) not in indexed[route]:
                raise ValueError("Example cites an unknown claim ID: " + case)
        require_text(row.get("finding"), "case finding")
        require_text(row.get("verdict"), "case verdict")
        data[case] = {"claims": claims, "indexed": indexed, "review": row, "direct_formal": formal}
    questions = review.get("research_questions", [])
    if {q["id"] for q in questions} != {"RQ0", "RQ1", "RQ2", "RQ3"} or len(questions) != 4:
        raise ValueError("Four authored research-question answers are required")
    for question in questions:
        require_text(question.get("question"), question["id"])
        require_text(question.get("answer"), question["id"])
    require_text(review.get("conclusion"), "conclusion")
    if not review.get("limitations") or not review.get("next_steps"):
        raise ValueError("Authored limitations and next steps are required")
    return run, review, references, data


# Load explanatory prose separately from immutable results and require honest provenance.
def load_briefing(path):
    briefing = read_json(path)
    for key in ("title", "subtitle", "prepared_on", "purpose", "method_note"):
        require_text(briefing.get(key), key)
    note = briefing["method_note"].lower()
    if "codex" not in note or not any(word in note for word in ("aussteh", "nicht", "keine")):
        raise ValueError("Briefing needs an explicit, factual method note about the recorded review")
    sections = briefing.get("sections", [])
    required_ids = {"overview", "motivation", "setup", "format", "method", "interpretation"}
    if {section.get("id") for section in sections} != required_ids or len(sections) != len(required_ids):
        raise ValueError("Briefing requires overview, motivation, setup, format, method and interpretation sections")
    for section in sections:
        require_text(section.get("title"), "section title")
        if not section.get("paragraphs"):
            raise ValueError("Briefing section needs explanatory paragraphs")
        for text in section["paragraphs"] + section.get("bullets", []):
            require_text(text, "section text")
    questions = briefing.get("research_questions", [])
    if {q.get("id") for q in questions} != {"RQ0", "RQ1", "RQ2", "RQ3"} or len(questions) != 4:
        raise ValueError("Briefing requires the four expanded research questions")
    for question in questions:
        for key in ("title", "question", "not_established"):
            require_text(question.get(key), "research question " + key)
        if not question.get("answer") or not question.get("evidence"):
            raise ValueError("Research question needs explanatory answers and evidence")
        for text in question["answer"] + question["evidence"]:
            require_text(text, "research question text")
    if set(briefing.get("case_explanations", {})) != set(CASES):
        raise ValueError("Briefing requires explanations for all three cases")
    for values in briefing["case_explanations"].values():
        for key in ("context", "baseline_scope", "takeaway"):
            if not values.get(key):
                raise ValueError("Case explanation needs " + key)
            for text in values[key]:
                require_text(text, "case explanation")
    if not briefing.get("glossary"):
        raise ValueError("Briefing requires a beginner glossary")
    return briefing


# Use readable Unicode fonts when present; keep portable built-in fallbacks.
def configure_styles():
    fonts = Path("/System/Library/Fonts/Supplemental")
    regular, bold = fonts / "Arial.ttf", fonts / "Arial Bold.ttf"
    family, mono = "Helvetica", "Courier"
    if regular.is_file() and bold.is_file():
        pdfmetrics.registerFont(TTFont("WCWC", str(regular)))
        pdfmetrics.registerFont(TTFont("WCWC-Bold", str(bold)))
        pdfmetrics.registerFontFamily("WCWC", normal="WCWC", bold="WCWC-Bold", italic="WCWC", boldItalic="WCWC-Bold")
        family = "WCWC"
    if (fonts / "Courier New.ttf").is_file():
        pdfmetrics.registerFont(TTFont("WCWC-Mono", str(fonts / "Courier New.ttf")))
        mono = "WCWC-Mono"
    bold_name = "WCWC-Bold" if family == "WCWC" else "Helvetica-Bold"
    normal = ParagraphStyle("Normal", fontName=family, fontSize=10.5, leading=14.2, textColor=NAVY, spaceAfter=7)
    styles = {"Normal": normal}
    styles["Title"] = ParagraphStyle("Title", parent=normal, fontName=bold_name, fontSize=27, leading=32, spaceAfter=10)
    styles["Subtitle"] = ParagraphStyle("Subtitle", parent=normal, fontSize=13, leading=18, textColor=GRAY, spaceAfter=12)
    styles["Heading1"] = ParagraphStyle("Heading1", parent=normal, fontName=bold_name, fontSize=17, leading=21, spaceBefore=16, spaceAfter=10, keepWithNext=True)
    styles["Heading2"] = ParagraphStyle("Heading2", parent=normal, fontName=bold_name, fontSize=12.5, leading=16, spaceBefore=12, spaceAfter=6, keepWithNext=True)
    styles["Heading3"] = ParagraphStyle("Heading3", parent=normal, fontName=bold_name, fontSize=10.5, leading=14, spaceBefore=9, spaceAfter=4, keepWithNext=True)
    styles["Small"] = ParagraphStyle("Small", parent=normal, fontSize=9, leading=12, textColor=GRAY, spaceAfter=6)
    styles["Cell"] = ParagraphStyle("Cell", parent=normal, fontSize=9.3, leading=12.1, spaceAfter=0)
    styles["Code"] = ParagraphStyle("Code", parent=normal, fontName=mono, fontSize=8.4, leading=11, leftIndent=7, rightIndent=7, borderPadding=7, backColor=PALE, spaceAfter=10)
    return styles, family


# Normalize only display typography; stored quotations and result files remain untouched.
def display_text(text):
    return str(text).replace("→", " -> ").replace("‑", "-").replace("–", "-").replace("—", "-").replace("`", "")


# Escape all source/review content before turning it into an editable-layout paragraph.
def paragraph(text, styles, style="Normal"):
    return Paragraph(escape(display_text(text)).replace("\n", "<br/>"), styles[style])


# Emphasize a short label while retaining the complete source statement after it.
def labelled(label, text, styles, style="Normal"):
    return Paragraph("<b>" + escape(label) + "</b> " + escape(display_text(text)).replace("\n", "<br/>"), styles[style])


# Draw workflow stages; arrows are data-processing paths, not proofs of higher claims.
def architecture(font):
    drawing = Drawing(WIDTH, 147)
    # Draw one workflow node without external assets.
    def box(x, y, width, label):
        drawing.add(Rect(x, y, width, 31, rx=5, fillColor=PALE, strokeColor=TEAL, strokeWidth=0.8))
        drawing.add(String(x + width / 2, y + 11, label, textAnchor="middle", fontName=font, fontSize=8.8, fillColor=NAVY))
    # Connect stages and place a small arrowhead at the receiving node.
    def arrow(x, y, end_x, end_y):
        drawing.add(Line(x, y, end_x, end_y, strokeColor=TEAL, strokeWidth=1.1))
        drawing.add(Polygon([end_x, end_y, end_x - 5, end_y + 2.5, end_x - 5, end_y - 2.5], fillColor=TEAL, strokeColor=TEAL))
    right = WIDTH - 99
    for x, y, width, label in [(0, 49, 74, "Quellcode"), (138, 94, 105, "Direkt: Claims"), (104, 4, 99, "Prosa-Report"), (245, 4, 100, "Prosa: Claims"), (right, 49, 99, "Vergleich"), (right, 110, 99, "Zielclaims zuerst")]:
        box(x, y, width, label)
    for coordinates in [(74, 68, 138, 109), (74, 60, 104, 19), (203, 19, 245, 19), (243, 109, right, 70), (345, 19, right, 58)]:
        arrow(*coordinates)
    drawing.add(Line(right + 49, 110, right + 49, 80, strokeColor=TEAL, strokeWidth=1.1))
    drawing.add(Polygon([right + 49, 80, right + 46.5, 85, right + 51.5, 85], fillColor=TEAL, strokeColor=TEAL))
    return drawing


# Create tables with repeatable headers and wrapped text; no semantic scores are inferred.
def table(rows, widths, styles):
    cells = [[paragraph(cell, styles, "Cell") for cell in row] for row in rows]
    result = Table(cells, colWidths=widths, hAlign="LEFT", repeatRows=1)
    result.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), PALE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 0.7, TEAL), ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#DCE5E9")), ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return result


# Keep a single clear provenance note near the beginning instead of repeating footers.
def method_box(text, styles):
    result = Table([[paragraph(text, styles)]], colWidths=[WIDTH], hAlign="LEFT")
    result.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE), ("BOX", (0, 0), (-1, -1), 0.6, TEAL), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    return result


# Render complete JSON with visual wrapping; its canonical bytes stay in the repository.
def code_block(value, styles):
    text = json.dumps(value, ensure_ascii=False, indent=2).replace("≤", "<=").replace("≥", ">=")
    return Preformatted(text, styles["Code"], maxLineLength=87, splitChars=" ", newLineChars="    ")


# Explain every field using the real common claim contract and a real frozen example.
def format_example(data, styles):
    claim = data["jspwiki"]["indexed"]["baseline"]["B02"]
    story = [KeepTogether([paragraph("Ein vollständiges JSON-Beispiel", styles, "Heading2"), paragraph("Dieses echte Beispiel stammt aus der vor dem Lauf fixierten JSPWiki-Referenz, Claim B02. Gezeigt ist ein einzelner Claim in der gemeinsamen Ausgabehülle. Lange Textzeilen sind für das PDF umgebrochen; die Originaldatei bleibt unverändert.", styles), code_block({"claims": [claim]}, styles)])]
    rows = [["Feld", "In einfachen Worten"]]
    meanings = [("claims", "Die Liste aller Claims einer Ausgabe. Eckige Klammern stehen für eine Liste; jeder Eintrag ist ein eigenes Objekt in geschweiften Klammern."), ("id", "Ein lokales Etikett. B02 bezeichnet hier einen Basisclaim. C2 einer anderen Route oder eines anderen Falls ist eine andere ID, auch wenn die Nummer ähnlich aussieht."), ("proposition", "Der eigentliche Aussagesatz. Er muss auch ohne Nachbarzeilen verständlich sein und notwendige Bedingungen selbst enthalten."), ("family / subtype", "Eine beschreibende Kategorie und gegebenenfalls ein Untertyp. null bedeutet hier: kein Untertyp vorgesehen. Es bedeutet nicht, dass die Aussage falsch ist."), ("family_reason", "Die kurze Begründung für die Kategorie. Sie ist keine Begründung dafür, dass die Proposition wahr ist."), ("qualifiers", "Zusätzliche Hinweise auf Bedingungen, Unsicherheit oder Scope. Sie dürfen eine im Aussagesatz fehlende Bedingung nicht ersetzen."), ("evidence", "Behauptete Quellenanker: Dateiname, Zeilen und exaktes Zitat. Beim Direktweg ist dies Code; beim Prosaweg ist es der neu erzeugte Report."), ("context_claim_ids", "Verweise, die das Verständnis erleichtern. Ein Verweis ist weder ein Beweis noch eine automatisch gültige logische Folgerung.")]
    rows += meanings
    story += [paragraph("So liest du das Format", styles, "Heading2"), table(rows, [104, WIDTH - 104], styles), paragraph("JSON ist die Verpackung. Eine formal korrekte Verpackung garantiert weder richtige Aussagen noch eine gute Zerlegung. Das Format ist ein kleiner, projektspezifischer Vertrag, kein allgemeiner Security-Standard.", styles)]
    return story


# Count exact source-anchor matches without changing the preserved acceptance decisions.
# This is a citation diagnostic, not a semantic judgment or a repaired model output.
def citation_diagnostics(run, data, styles):
    manifest = read_json(ROOT / "examples/sources.json")
    rows = [["Direkte Rohantwort", "Exakte Zitate", "Abweichende Zitate", "Ganze Datei"]]
    exact_total, wrong_total = 0, 0
    for case in CASES:
        sources = {}
        for entry in manifest["files"]:
            if entry["role"] == "allowed_code" and entry["path"].startswith(case + "/"):
                path = ROOT / "examples" / entry["path"]
                if hashlib.sha256(path.read_bytes()).hexdigest() != run["code_hashes"][case][entry["path"]]:
                    raise ValueError("Source bytes changed: " + entry["path"])
                sources[path.name] = (entry["original_lines"][0], path.read_text(encoding="utf-8").splitlines())
        exact, wrong = 0, 0
        for claim in data[case]["claims"]["direct"]:
            for ref in claim["evidence"]:
                offset, lines = sources[ref["file"]]
                first, last = ref["line_start"], ref["line_end"]
                valid_range = offset <= first <= last < offset + len(lines)
                excerpt = "\n".join(lines[first - offset:last - offset + 1]) if valid_range else ""
                valid = bool(ref["quote"]) and valid_range and ref["quote"] in excerpt
                exact += int(valid)
                wrong += int(not valid)
        exact_total += exact
        wrong_total += wrong
        rows.append([NAMES[case], exact, wrong, "angenommen" if data[case]["direct_formal"] == "completed" else "abgelehnt"])
    rows.append(["Summe Quellenanker", exact_total, wrong_total, "keine Umwertung"])
    story = [paragraph("Warum drei Dateien scheitern, obwohl viele Zitate stimmen", styles, "Heading2"), table(rows, [WIDTH * f for f in (.32, .19, .24, .25)], styles)]
    explanations = [
        "Gezählt werden hier evidence-Einträge, nicht Claims. Ein Claim kann mehrere Quellenanker haben. Diese Diagnose liest dieselben unveränderten Antworten erneut; die vorherige Ablehnung wird dadurch nicht aufgehoben.",
        "JSPWiki, Direkt C9: Ein vermeintliches Originalzitat aus web.xml enthält eine eigene Zeile mit drei Punkten als Auslassung. Diese Zeile steht so nicht im Quelltext. Ein gekürztes Exzerpt kann verständlich sein, erfüllt aber den hier verlangten exakten Zitiervertrag nicht.",
        "Jackson, Direkt C2: Der fehlerhafte Anker nennt Originalzeilen 138-143, zitiert aber noch die schließende Klammer aus Zeile 144. Der andere Quellenanker dieses Claims kann gleichzeitig korrekt sein. Die beschriebene Setter-Operation wird durch die falsche Endzeile nicht automatisch widerlegt.",
        "YAML, Direkt C1: Die zitierten drei Ladeoperationen existieren, aber im mehrzeiligen Modellzitat fehlt Einrückung. Der Vertrag verlangt eine zusammenhängend exakt gleiche Zeichenfolge. Hier scheitert daher zunächst die Quellenübernahme, nicht zwingend der fachliche Inhalt.",
        "YAML, Direkt C6: Zusätzlich zur Zitatfrage enthält der Rohclaim family=unclear und subtype=unclear. Nach der lokalen Feldregel darf subtype nur für exploitability_impact gesetzt sein; sonst ist null verlangt. Ein Zeilenbereich verweist außerdem neben die Map-Zuweisung. Das gespeicherte Laufprotokoll meldet nur den ersten gefundenen Fehler; diese zusätzlichen Beobachtungen reparieren nichts.",
        "Ein weniger strenger künftiger Zitiervertrag könnte reine Darstellungsunterschiede anders behandeln. Das wäre eine vorab festzulegende Änderung für einen neuen Versuch. Den bestehenden Test nach Sicht auf seine Fehler still abzuschwächen, würde diesen Vergleich verfälschen."
    ]
    story += [paragraph(text, styles) for text in explanations]
    return story


# Summarize only previously authored labels, keeping output validity separate from coverage.
def result_tables(run, data, styles):
    story = [paragraph("Was technisch angenommen oder abgelehnt wurde", styles, "Heading2")]
    rows = [["Fall und Weg", "Aussagen", "Formale Annahme", "Welche Quelle wurde geprüft?"]]
    for case in CASES:
        item = data[case]
        for route, name in (("direct", "Direkt"), ("prose", "Prosa")):
            accepted = route == "prose" or item["direct_formal"] == "completed"
            rows.append([NAMES[case] + "\n" + name, len(item["claims"][route]), "angenommen" if accepted else "nicht angenommen", "Textzitate im Report" if route == "prose" else "Codezitate und ihre Zeilen"])
    story.append(table(rows, [WIDTH * .27, WIDTH * .11, WIDTH * .25, WIDTH * .37], styles))
    story.append(paragraph("Die Direktantworten sind lesbare Rohantworten mit JSON-Struktur. Trotzdem ist jeweils mindestens ein Quellenanker nicht vertragsgemäß, weshalb die ganze Ausgabedatei abgelehnt wurde. Das ist nicht gleichbedeutend mit: Jeder enthaltene Satz ist fachlich falsch. Umgekehrt beweist ein korrektes Reportzitat nur ein Textvorkommen, nicht die Wahrheit einer Codebehauptung.", styles))
    story.extend(citation_diagnostics(run, data, styles))
    story.append(paragraph("Wie viele Zielinhalte in den Aussagen wiederzufinden waren", styles, "Heading2"))
    rows = [["Fall", "Weg", "Zielinhalte", "Vollständig", "Teilweise", "Fehlend"]]
    totals = {route: Counter() for route in ("direct", "prose")}
    for case in CASES:
        row = data[case]["review"]
        for route, name in (("direct", "Direkt"), ("prose", "Prosa")):
            counts = Counter(r[route]["coverage"] for r in row["baseline_assessment"])
            totals[route].update(counts)
            rows.append([NAMES[case], name, len(row["baseline_assessment"]), counts["full"], counts["partial"], counts["missing"]])
    for route, name in (("direct", "Direkt"), ("prose", "Prosa")):
        counts = totals[route]
        rows.append(["Alle drei Fälle", name, sum(counts.values()), counts["full"], counts["partial"], counts["missing"]])
    story.append(table(rows, [WIDTH * f for f in (.24, .12, .14, .17, .17, .16)], styles))
    explanations = ["Vollständig: Der gemeinte Inhalt einschließlich seiner nötigen Bedingungen ist erfasst. Mehrere Modellclaims dürfen gemeinsam einen Basisclaim abdecken.", "Teilweise: Ein relevanter Teil ist erfasst, aber beispielsweise ein Zweig, eine Voraussetzung, die genaue Datenquelle oder eine Abgrenzung fehlt.", "Fehlend: In den Propositionen wurde keine passende Aussage gefunden. Eine Information nur im langen Quellenzitat ersetzt keinen ausformulierten Claim.", "Die Summen zählen dieselben " + str(sum(len(data[c]["review"]["baseline_assessment"]) for c in CASES)) + " Zielinhalte je Weg, nicht zwei getrennte Zielmengen. Die Direktzuordnung ist eine diagnostische Betrachtung formal abgelehnter Rohclaims. Die Kategorien sind begründete Einzelurteile aus review.json, keine berechnete Ähnlichkeit und kein statistischer Qualitätsscore."]
    story += [paragraph(text, styles) for text in explanations]
    cost = ("%.3f" % run["spent_estimate_usd"]).replace(".", ",")
    story.append(paragraph("Tatsächlich ausgeführt wurden neun API-Aufrufe: drei direkte Claim-Aufrufe sowie je drei Reporterzeugungen und Reportzerlegungen. Geschätzte Kosten: " + cost + " USD. Es gab keine Wiederholung bis zu einem gewünschten Ergebnis.", styles))
    return story


# Render every frozen target and the two route-specific, individually reasoned mappings.
def case_detail(case, item, explanation, styles):
    story = []
    for text in explanation["context"]:
        story.append(paragraph(text, styles))
    story.append(paragraph("Welche Inhalte die Zielreferenz hier fordert", styles, "Heading2"))
    story += [paragraph("• " + text, styles) for text in explanation["baseline_scope"]]
    example = item["review"]["example"]
    story.append(paragraph("Ein Beispiel direkt nebeneinander", styles, "Heading2"))
    for route, key, label in (("baseline", "baseline_id", "Zielclaim"), ("direct", "direct_id", "Direkte Rohantwort"), ("prose", "prose_id", "Aus dem Report extrahiert")):
        claim = item["indexed"][route][example[key]]
        story.append(labelled(label + " " + claim["id"] + ":", claim["proposition"], styles))
    story.append(labelled("Einordnung:", example.get("comment", item["review"]["finding"]), styles))
    story.append(paragraph("Alle Zielclaims dieses Falls und ihre Zuordnung", styles, "Heading2"))
    coverage_names = {"full": "vollständig", "partial": "teilweise", "missing": "fehlend"}
    for assessment in item["review"]["baseline_assessment"]:
        claim = item["indexed"]["baseline"][assessment["baseline_id"]]
        block = [paragraph(claim["id"] + " - Zielaussage", styles, "Heading3"), paragraph(claim["proposition"], styles)]
        for route, label in (("direct", "Direkt"), ("prose", "Prosa")):
            judgment = assessment[route]
            ids = ", ".join(judgment["ids"]) or "keine zugeordneten Claims"
            block.append(labelled(label + ": " + coverage_names[judgment["coverage"]] + " (" + ids + ").", judgment["reason"], styles))
        story.append(KeepTogether(block))
    story.append(paragraph("Was du aus diesem Fall mitnehmen kannst", styles, "Heading2"))
    story += [paragraph(text, styles) for text in explanation["takeaway"]]
    return story


# Present all generated statements and recorded judgments without repairing raw evidence.
def generated_appendix(data, styles):
    count = sum(len(data[c]["claims"][r]) for c in CASES for r in ("direct", "prose"))
    story = [paragraph("Hier stehen die " + str(count) + " tatsächlich erzeugten Propositionen mit den im Versuch gespeicherten Einzelbegründungen. Die jeweiligen Rohantworten bleiben unverändert. Die Fundstellen unten sind die vom Modell angegebenen Quellenanker; ihre Darstellung macht einen abgelehnten Anker nicht gültig.", styles)]
    support = {"supported": "im gegebenen Code gestützt", "inconclusive": "mit dem Ausschnitt nicht entscheidbar", "contradicted": "durch den Code widersprochen", "mixed": "teils gestützt, teils zu weit oder offen"}
    granularity = {"acceptable": "als Einheit vertretbar", "too_broad": "zu breit oder mehrere Inhalte vermischt", "fragment": "zu fragmentarisch"}
    faithful = {"yes": "ja", "partial": "teilweise", "no": "nein"}
    for index, case in enumerate(CASES):
        if index:
            story.append(CondPageBreak(200))
        story.append(paragraph(NAMES[case] + " - vollständige Modellpropositionen", styles, "Heading2"))
        for route, name in (("direct", "Direkte Rohantwort"), ("prose", "Prosa-Extraktion")):
            story += [paragraph(name, styles, "Heading2")]
            if route == "direct" and data[case]["direct_formal"] != "completed":
                story.append(paragraph("Diese gesamte Direkt-Ausgabe wurde formal nicht angenommen. Die folgenden Sätze werden ausschließlich inhaltlich diagnostisch betrachtet.", styles, "Small"))
            judgments = {row["id"]: row for row in data[case]["review"]["generated_claim_assessment"][route]}
            for claim in data[case]["claims"][route]:
                row = judgments[claim["id"]]
                block = [paragraph(NAMES[case] + " / " + ("Direkt" if route == "direct" else "Prosa") + " / " + claim["id"], styles, "Heading3"), paragraph(claim["proposition"], styles)]
                labels = "Codeunterstützung: " + support[row["code_support"]] + ". Granularität: " + granularity[row["granularity"]] + "."
                if route == "prose":
                    labels += " Reporttreue: " + faithful[row["report_faithful"]] + "."
                block.append(paragraph(labels, styles, "Small"))
                block.append(labelled("Begründung:", row["reason"], styles))
                refs = [ref["file"] + ":" + str(ref["line_start"]) + "-" + str(ref["line_end"]) for ref in claim.get("evidence", [])]
                block.append(paragraph("Angegebene Quellenanker: " + "; ".join(refs), styles, "Small"))
                story.append(KeepTogether(block))
    return story


# Show the exact saved task instructions so the prompting method is inspectable.
def prompt_appendix(styles):
    prompts = read_json(ROOT / "resources/prompts.json")
    story = [paragraph("Dies sind die im Lauf verwendeten Aufgabentexte. Für Code-Claims und Report-Claims werden jeweils die gemeinsamen Claim-Regeln angehängt. Die Reporterzeugung erhält nur ihren eigenen Aufgabentext. Die JSON-Schemavorgabe ist zusätzlich Teil des gespeicherten API-Requests.", styles)]
    names = {"code_claims": "Direkt aus Code Claims erzeugen", "code_report": "Aus Code einen kurzen Report erzeugen", "report_claims": "Den Report in Claims zerlegen", "common_claim_rules": "Gemeinsame Regeln für die Claim-Ausgaben"}
    for key in ("code_claims", "code_report", "report_claims", "common_claim_rules"):
        story += [paragraph(names[key], styles, "Heading2"), paragraph(prompts[key], styles)]
    return story


# Make every source clickable and retain its stated evidence limits in the briefing.
def bibliography(references, styles):
    story = []
    for item in references["literature"]:
        authors = ", ".join(item.get("authors", []))
        year = str(item.get("year")) if item.get("year") is not None else "ohne Jahresangabe"
        label = authors + " (" + year + "). " + item["title"]
        url = item.get("url") or item.get("full_text")
        block = [Paragraph('<b>[' + escape(item["id"]) + ']</b> <link href="' + escape(url) + '" color="#087F8C">' + escape(label) + "</link>", styles["Normal"])]
        if item.get("supports"):
            block.append(labelled("Wofür die Quelle hier herangezogen wird:", item["supports"], styles, "Small"))
        if item.get("does_not_support"):
            block.append(labelled("Begrenzung:", item["does_not_support"], styles, "Small"))
        story.append(KeepTogether(block))
    dataset = references["dataset"]
    story += [paragraph("Dataset und konkrete Codebeispiele", styles, "Heading2"), Paragraph('<link href="' + escape(dataset["url"]) + '" color="#087F8C">Vul4J - fixierte Datasetfassung</link>', styles["Normal"]), paragraph("Revision: " + dataset["revision"] + ". Lizenz: " + dataset["license"] + ".", styles, "Small")]
    for item in references["cases"]:
        story.append(labelled(NAMES[item["id"]] + " (" + item["vul4j_id"] + "):", item["input_scope"], styles))
        story.append(Paragraph('<link href="' + escape(item["pov_source"]) + '" color="#087F8C">Historische PoV-Testquelle dieses Falls</link>', styles["Small"]))
    return story


# Compose the reader-facing explanation first, then exhaustive evidence-based appendices.
def build_story(run, review, references, data, briefing, styles, font):
    p = lambda text, style="Normal": paragraph(text, styles, style)
    story = [p(briefing["title"], "Title"), p(briefing["subtitle"], "Subtitle"), p("Persönliches Briefing | Stand " + briefing["prepared_on"], "Small"), p(briefing["purpose"])]
    story += [p("Methodeneinordnung", "Heading2"), method_box(briefing["method_note"], styles), Spacer(1, 12), p("So kannst du dieses Dokument lesen", "Heading2")]
    target_count = sum(len(data[c]["claims"]["baseline"]) for c in CASES)
    generated_count = sum(len(data[c]["claims"][r]) for c in CASES for r in ("direct", "prose"))
    guide = ["Für den Überblick: Lies zuerst die Erklärung des Problems, die beiden Wege und die Ergebnistabellen.", "Für eine konkrete Diskussion: Lies das jeweilige Fallkapitel. Dort stehen alle " + str(target_count) + " Zielinhalte und die begründeten Zuordnungen.", "Für jede einzelne Modellaussage: Nutze Anhang A mit allen " + str(generated_count) + " Propositionen. Anhang B enthält die tatsächlichen Prompts.", "Unklare Begriffe sind am Ende des Hauptteils kurz erklärt. Die Quellenlinks stehen ganz am Ende.", "Die PDF-Lesezeichen führen direkt zu den Kapiteln. Erklärteil und Forschungsfragen kannst du zuerst lesen; die vollständigen Einzelbegründungen sind zum Nachschlagen gedacht."]
    story += [p("• " + text) for text in guide]
    story.append(table([["Fälle", "Vorher fixierte Zielclaims", "Erzeugte Propositionen", "API-Aufrufe"], [3, sum(len(data[c]["claims"]["baseline"]) for c in CASES), sum(len(data[c]["claims"][r]) for c in CASES for r in ("direct", "prose")), len(run["tasks"])]], [WIDTH * .15, WIDTH * .29, WIDTH * .30, WIDTH * .26], styles))
    story.append(p("Diese Anzahlen beschreiben den Umfang. Sie sind für sich genommen kein Qualitätsmaß.", "Small"))
    story.append(PageBreak())
    chapter = 0
    for section in briefing["sections"]:
        chapter += 1
        story += [CondPageBreak(150), p(str(chapter) + ". " + section["title"], "Heading1")]
        story += [p(text) for text in section["paragraphs"]]
        story += [p("• " + text) for text in section.get("bullets", [])]
        if section["id"] == "setup":
            story += [architecture(font), p("Pfeile zeigen hier einen Verarbeitungsschritt. Sie beweisen keine Sicherheitswirkung und keinen höheren Claim.", "Small")]
            rows = [["Fall", "Erlaubter Codekontext"]] + [[NAMES[item["id"]] + "\n" + item["vul4j_id"], item["input_scope"]] for item in references["cases"]]
            story.append(table(rows, [112, WIDTH - 112], styles))
            model = run["model"] + "; Reasoning-Einstellung " + run["reasoning_effort"] + "; Ausgabelimit " + str(run["max_claim_tokens"]) + " Tokens für Claims und " + str(run["max_report_tokens"]) + " für Reports."
            story.append(labelled("Konkrete Laufkonfiguration:", model, styles))
        if section["id"] == "format":
            story.extend(format_example(data, styles))
    chapter += 1
    story += [CondPageBreak(240), p(str(chapter) + ". Die tatsächlichen Ergebnisse lesen", "Heading1")]
    story.extend(result_tables(run, data, styles))
    for case in CASES:
        chapter += 1
        story += [CondPageBreak(240), p(str(chapter) + ". " + NAMES[case] + " im Detail", "Heading1")]
        story.extend(case_detail(case, data[case], briefing["case_explanations"][case], styles))
    chapter += 1
    story += [CondPageBreak(240), p(str(chapter) + ". Forschungsfragen ausführlich beantwortet", "Heading1")]
    for question in sorted(briefing["research_questions"], key=lambda q: q["id"]):
        story += [CondPageBreak(160), p(question["id"] + " - " + question["title"], "Heading2"), labelled("Die Frage:", question["question"], styles)]
        story += [p(text) for text in question["answer"]]
        story.append(p("Worauf diese Antwort beruht", "Heading3"))
        story += [p("• " + text) for text in question["evidence"]]
        story += [p("Was damit nicht gezeigt wurde", "Heading3"), p(question["not_established"])]
    chapter += 1
    story += [p(str(chapter) + ". Fazit und nächster sinnvoller Schritt", "Heading1"), p(review["conclusion"])]
    story += [p("• " + text) for text in review["limitations"]]
    story += [p(text) for text in review["next_steps"]]
    chapter += 1
    story += [PageBreak(), p(str(chapter) + ". Begriffe zum Nachschlagen", "Heading1")]
    story.append(table([["Begriff", "Bedeutung"]] + [[row["term"], row["meaning"]] for row in briefing["glossary"]], [113, WIDTH - 113], styles))
    story += [PageBreak(), p("Anhang A - alle erzeugten Aussagen", "Heading1")]
    story.extend(generated_appendix(data, styles))
    story += [PageBreak(), p("Anhang B - die tatsächlich verwendeten Prompts", "Heading1")]
    story.extend(prompt_appendix(styles))
    story += [PageBreak(), p("Quellen und Herkunft", "Heading1")]
    story.extend(bibliography(references, styles))
    return story


# Keep running pages quiet; provenance is explained explicitly near the beginning.
def footer(canvas, doc):
    canvas.setStrokeColor(TEAL)
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(18 * mm, 9 * mm, "WCWC | Persönliches Briefing")
    canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, "Seite " + str(doc.page))


# Add navigation bookmarks for major chapters in the long personal briefing.
class BriefingDocument(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("Title", "Heading1"):
            number = getattr(self, "bookmark_count", 0) + 1
            self.bookmark_count = number
            key = "chapter-" + str(number)
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.getPlainText(), key, level=0, closed=False)


# Validate sources first, then replace the long A4 briefing atomically after compilation.
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=ROOT / "results/run-001")
    parser.add_argument("--output", type=Path, default=ROOT / "output/pdf/wcwc-ergebnisse.pdf")
    parser.add_argument("--briefing", type=Path, default=ROOT / "resources/briefing.json")
    args = parser.parse_args()
    run, review, references, data = load_data(args.run)
    briefing = load_briefing(args.briefing)
    styles, font = configure_styles()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp.pdf")
    document = BriefingDocument(str(temporary), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=20 * mm, title=briefing["title"] + " - persönliches Briefing", author="WCWC / Codex, KI-unterstützt")
    try:
        document.build(build_story(run, review, references, data, briefing, styles, font), onFirstPage=footer, onLaterPages=footer)
        pages = PdfReader(str(temporary)).pages
        if not pages or any(abs(float(page.mediabox.width) - A4[0]) > 1 or abs(float(page.mediabox.height) - A4[1]) > 1 for page in pages):
            raise ValueError("Expected nonempty A4 briefing")
        temporary.replace(args.output)
    finally:
        temporary.unlink(missing_ok=True)
    print(str(args.output) + " (" + str(len(pages)) + " A4-Seiten)")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise SystemExit("PDF not created: " + str(error)) from error
