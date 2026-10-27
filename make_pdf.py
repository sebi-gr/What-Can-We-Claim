"""Build a three-page German overview from an explicitly authored claim review."""

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
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
CASES = ("jspwiki", "jackson-xml", "commons-yaml")
NAMES = {"jspwiki": "JSPWiki", "jackson-xml": "Jackson XML", "commons-yaml": "Commons YAML"}
NAVY, TEAL = colors.HexColor("#17324D"), colors.HexColor("#087F8C")
GRAY, PALE = colors.HexColor("#536373"), colors.HexColor("#EDF5F7")
WIDTH = A4[0] - 30 * mm


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


# Use a Unicode font when available; core Helvetica remains a portable fallback.
def configure_styles():
    fonts = Path("/System/Library/Fonts/Supplemental")
    regular, bold = fonts / "Arial.ttf", fonts / "Arial Bold.ttf"
    family = "Helvetica"
    if regular.is_file() and bold.is_file():
        pdfmetrics.registerFont(TTFont("WCWV", str(regular)))
        pdfmetrics.registerFont(TTFont("WCWV-Bold", str(bold)))
        pdfmetrics.registerFontFamily("WCWV", normal="WCWV", bold="WCWV-Bold", italic="WCWV", boldItalic="WCWV-Bold")
        family = "WCWV"
    styles = {}
    for name in ("Normal", "BodyText"):
        styles[name] = ParagraphStyle(name, fontName=family, fontSize=10, leading=12.6, textColor=NAVY, spaceAfter=6)
    styles["Title"] = ParagraphStyle("Title", parent=styles["Normal"], fontSize=21, leading=24, spaceAfter=8)
    styles["Heading2"] = ParagraphStyle("Heading2", parent=styles["Normal"], fontName=family + "-Bold" if family == "WCWV" else "Helvetica-Bold", fontSize=12, leading=14.5, spaceBefore=10, spaceAfter=5)
    styles["Small"] = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8.8, leading=11, textColor=GRAY, spaceAfter=4)
    styles["Cell"] = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=9, leading=11, spaceAfter=0)
    return styles, family


# Escape all source/review text; literal arrows and uncommon dashes become portable text.
def paragraph(text, styles, style="Normal"):
    value = str(text).replace("→", " > ").replace("‑", "-").replace("–", "-").replace("—", "-").replace("`", "")
    return Paragraph(escape(value).replace("\n", "<br/>"), styles[style])


# Draw a small architecture diagram; connectors denote workflow, never logical proof.
def architecture(font):
    drawing = Drawing(WIDTH, 145)
    # Place a readable workflow node without importing visual assets.
    def box(x, y, width, label, fill=PALE):
        drawing.add(Rect(x, y, width, 31, rx=5, fillColor=fill, strokeColor=TEAL, strokeWidth=0.8))
        drawing.add(String(x + width / 2, y + 11, label, textAnchor="middle", fontName=font, fontSize=9, fillColor=NAVY))
    # Connect workflow stages; these lines do not claim logical entailment.
    def arrow(x, y, end_x, end_y):
        drawing.add(Line(x, y, end_x, end_y, strokeColor=TEAL, strokeWidth=1.1))
        drawing.add(Polygon([end_x, end_y, end_x - 5, end_y + 2.5, end_x - 5, end_y - 2.5], fillColor=TEAL, strokeColor=TEAL))
    right = WIDTH - 104
    for x, y, width, label in [(0, 49, 80, "Source Code"), (148, 94, 111, "Direkt: Claims"), (116, 4, 104, "Prosa-Report"), (264, 4, 105, "Prosa: Claims"), (right, 49, 104, "Vergleich"), (right, 110, 104, "Zielclaims zuerst")]:
        box(x, y, width, label)
    for coordinates in [(80, 68, 148, 109), (80, 60, 116, 19), (220, 19, 264, 19), (259, 109, right, 70), (369, 19, right, 58)]:
        arrow(*coordinates)
    drawing.add(Line(right + 52, 110, right + 52, 80, strokeColor=TEAL, strokeWidth=1.1))
    drawing.add(Polygon([right + 52, 80, right + 49.5, 85, right + 54.5, 85], fillColor=TEAL, strokeColor=TEAL))
    return drawing


# Format only explicitly authored coverage labels; no lexical matching or AI judging.
def coverage_text(row, route):
    counts = Counter(item[route]["coverage"] for item in row["baseline_assessment"])
    return "/".join(str(counts[key]) for key in ("full", "partial", "missing"))


# Apply consistent quiet table styling while keeping explanatory text wrapped.
def table(rows, widths, styles):
    result = Table([[paragraph(cell, styles, "Cell") for cell in row] for row in rows], colWidths=widths, hAlign="LEFT")
    result.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), PALE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 0.7, TEAL), ("LINEBELOW", (0, 1), (-1, -1), 0.35, colors.HexColor("#DCE5E9")), ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return result


# Compose three explicit pages; full example propositions retain their conditions.
def build_story(run, review, references, data, styles, font):
    p = lambda text, style="Normal": paragraph(text, styles, style)
    story = [p("Sicherheitsclaims aus Code", "Title"), p("Drei Entwicklungsfälle - direkter Weg und Prosa-Zwischenschritt", "Small")]
    story += [p("Warum einzelne Claims?", "Heading2"), p("Ein ganzer Report kann richtige Codebeobachtungen und unbelegte Angriffswirkungen vermischen. Einzelne, eigenständig verständliche Aussagen erlauben gezielte Teilurteile: Was ist belegt, was fehlt und welche Bedingung wurde verändert? Kontext und Evidenz bleiben sichtbar [1-3]. IDs und Git machen Änderungen nachvollziehbar; Claims sind nicht von sich aus versioniert.")]
    story += [architecture(font), p("Beide Wege verwenden dieselben Codebytes. Der Vergleich greift auf vorher fixierte Zielclaims zu; die Generierung erhält diese Referenz nicht. Untersucht werden Inhalte und Erzeugungswege, nicht nur eine Formatumwandlung [4].", "Small")]
    cases = {c["id"]: c for c in references["cases"]}
    rows = [["Fall", "Bereitgestellter Code / Grenze"]]
    scopes = {"jspwiki": "Fünf vollständige Dateien; WikiEngine, Filter und Ziel-JSPs fehlen.", "jackson-xml": "XmlFactory.java, Originalzeilen 84-144; Provider und Aufrufer fehlen.", "commons-yaml": "YAMLConfiguration.java vollständig; SnakeYAML und Aufrufer fehlen."}
    rows += [[NAMES[c] + "\n" + cases[c]["vul4j_id"], scopes[c]] for c in CASES]
    story += [p("Drei Beispiele aus Vul4J [5]", "Heading2"), table(rows, [116, WIDTH - 116], styles)]
    story += [p("Was sind die Basis- oder Zielclaims?", "Heading2"), p("Codegestützte Sollinhalte nach dem Muster der früheren SG-Annotation: etwa JSPWiki-Pfad versus Query, Jacksons bedingte Factory-Konfiguration und YAML-Ladepfade mit bzw. ohne Optionen. Das gemeinsame JSON enthält ID, Proposition, Familie, Begründung, Bedingungen/Scope, Quellenzitate mit Zeilen und Kontextbezüge. Bedingungen stehen auch im Satz; keine feste Claimzahl.")]
    story += [p("Wie wurde geprüft?", "Heading2"), p("Zielreferenz und semantischer Vergleich sind KI-unterstützte Entwürfe von Codex; menschliches Gegenlesen steht aus. Die historischen SG-Claims sind keine unabhängige Codereferenz. Automatisch werden Format, Zitate und Referenzen geprüft. Formal abgelehnte Rohclaims bleiben abgelehnt; ihre Propositionen werden nur diagnostisch gegengelesen. Inhaltliche Zuordnungen sind einzeln begründet, ohne automatisches Matching.")]
    cost = ("%.3f" % run["spent_estimate_usd"]).replace(".", ",")
    story += [p("Modell: " + run["model"] + "; ein Lauf je Fall und Weg, insgesamt neun API-Aufrufe ohne Retry. Geschätzte API-Kosten: " + cost + " USD bei 1 USD Kostenrahmen. Keine neuen Java-/PoV-Läufe.", "Small"), PageBreak()]
    story += [p("Ergebnisse im direkten Vergleich", "Title"), p("Deskriptive Zusammenfassung der eingetragenen KI-Bewertung; keine menschlichen Messurteile.", "Small")]
    rows = [["Fall", "Basis", "Direkt:\nRohclaims / Form", "Prosa:\nClaims / Form", "Abdeckung D\nV/T/F", "Abdeckung P\nV/T/F"]]
    for case in CASES:
        item = data[case]
        form = "gültig" if item["direct_formal"] == "completed" else "abgelehnt"
        rows.append([NAMES[case], len(item["claims"]["baseline"]), str(len(item["claims"]["direct"])) + " / " + form, str(len(item["claims"]["prose"])) + " / gültig", coverage_text(item["review"], "direct"), coverage_text(item["review"], "prose")])
    story += [table(rows, [97, 35, 80, 80, (WIDTH - 292) / 2, (WIDTH - 292) / 2], styles), p("V/T/F = vollständig / teilweise / fehlend abgedeckte Zielinhalte. Bei abgelehnter Direkt-Ausgabe ist diese Zuordnung nur eine Rohclaim-Diagnose. Prosa-Zitate verweisen auf den Report; Reporttreue und Codeunterstützung werden gesondert beurteilt. Claimzahl ist kein Qualitätsscore; mehrere Claims können gemeinsam einen Inhalt abdecken.", "Small")]
    for case in CASES:
        item, example = data[case], data[case]["review"]["example"]
        block = [p(NAMES[case] + ": konkretes Beispiel", "Heading2")]
        for route, key, label in (("baseline", "baseline_id", "Basis"), ("direct", "direct_id", "Direkt-Rohclaim"), ("prose", "prose_id", "Prosa")):
            claim = item["indexed"][route][example[key]]
            block.append(p(label + " " + claim["id"] + ": " + claim["proposition"]))
        block.append(p("Befund: " + item["review"]["finding"], "Small"))
        story.append(KeepTogether(block))
    story += [PageBreak(), p("Antworten und Reichweite", "Title")]
    for question in sorted(review["research_questions"], key=lambda q: q["id"]):
        story += [p(question["id"] + " - " + question["question"], "Heading2"), p(question["answer"])]
    story += [p("Gesamtfazit", "Heading2"), p(review["conclusion"]), p("Grenzen und nächster Schritt", "Heading2")]
    story += [p("• " + text, "Small") for text in review["limitations"]]
    story.append(p("Nächster Schritt: " + " ".join(review["next_steps"])))
    story += [p("Primärquellen", "Heading2")]
    refs = {item["id"]: item for item in references["literature"]}
    for number, key in enumerate(("wanner2024", "song2024", "sacm22", "tam2024"), 1):
        item = refs[key]
        label = item["authors"][0] + (" et al." if len(item["authors"]) > 1 else "") + " (" + str(item["year"]) + "). " + item["title"]
        story.append(Paragraph("[" + str(number) + "] <link href=" + '"' + escape(item["url"]) + '" color="#087F8C">' + escape(label) + "</link>", styles["Small"]))
    story.append(Paragraph('[5] <link href="' + escape(references["dataset"]["url"]) + '" color="#087F8C">Vul4J: fixierte Datasetfassung und drei ausgewählte Fälle.</link>', styles["Small"]))
    return story


# Add unobtrusive page numbering; abort if long review text would silently overflow.
def footer(canvas, doc):
    if doc.page > 3:
        raise ValueError("Review text exceeds three A4 pages; shorten findings/answers, not claim conditions")
    canvas.setStrokeColor(TEAL)
    canvas.line(15 * mm, 14 * mm, A4[0] - 15 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(15 * mm, 9 * mm, "WCWV | KI-unterstützter Entwicklungsvergleich | Menschliche Kontrolle ausstehend")
    canvas.drawRightString(A4[0] - 15 * mm, 9 * mm, str(doc.page) + " / 3")


# Author only after complete validation; replace the PDF atomically after a page check.
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=ROOT / "results/run-001")
    parser.add_argument("--output", type=Path, default=ROOT / "output/pdf/wcwv-ergebnisse.pdf")
    args = parser.parse_args()
    run, review, references, data = load_data(args.run)
    styles, font = configure_styles()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp.pdf")
    document = SimpleDocTemplate(str(temporary), pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm, topMargin=13 * mm, bottomMargin=20 * mm, title="Sicherheitsclaims aus Code - drei Entwicklungsfälle", author="WCWV / Codex, KI-unterstützt")
    try:
        document.build(build_story(run, review, references, data, styles, font), onFirstPage=footer, onLaterPages=footer)
        pages = PdfReader(str(temporary)).pages
        if len(pages) != 3 or any(abs(float(page.mediabox.width) - A4[0]) > 1 or abs(float(page.mediabox.height) - A4[1]) > 1 for page in pages):
            raise ValueError("Expected exactly three A4 pages")
        temporary.replace(args.output)
    finally:
        temporary.unlink(missing_ok=True)
    print(args.output)


if __name__ == "__main__":
    try:
        main()
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise SystemExit("PDF not created: " + str(error)) from error
