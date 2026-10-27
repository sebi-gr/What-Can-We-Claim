"""Run the three-case claim experiment once, with explicit cost and context limits."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
CASES = ("jspwiki", "jackson-xml", "commons-yaml")
MODEL = "gpt-5.4-mini-2026-03-17"
PRICES = {"input": 0.75, "output": 4.50}
CLAIM_TOKENS, REPORT_TOKENS = 8192, 2048
REPORT_BYTES, REPORT_LINES = 32000, 512


# Return a SHA-256 digest of original bytes, without printing their contents.
def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Replace one small artifact atomically; never include authentication headers.
def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


# Read only manifest-whitelisted code; return numbered text, quote sources and hashes.
# Original excerpt offsets are retained; symlinks and changed source bytes are rejected.
def build_code_context(case, root=ROOT):
    if case not in CASES:
        raise ValueError("Unknown case")
    examples = root / "examples"
    manifest = json.loads((examples / "sources.json").read_text(encoding="utf-8"))
    sources, hashes, parts = {}, {}, []
    for entry in manifest["files"]:
        if entry["role"] != "allowed_code" or Path(entry["path"]).parts[0] != case:
            continue
        path = examples / entry["path"]
        allowed = examples / case / "code"
        if path.parent != allowed or path.resolve() != path or not path.is_file():
            raise ValueError("Unsafe code path")
        digest = file_hash(path)
        if digest != entry["sha256"]:
            raise ValueError("Source hash mismatch: " + path.name)
        text = path.read_bytes().decode("utf-8")
        start, end = entry["original_lines"]
        lines = text.splitlines()
        if len(lines) != end - start + 1 or path.name in sources:
            raise ValueError("Source range or filename mismatch")
        sources[path.name] = {"line_start": start, "text": text}
        hashes[entry["path"]] = digest
        parts.append("FILE " + path.name + "\n" + "\n".join(
            str(number) + " | " + line for number, line in enumerate(lines, start)))
    if not sources:
        raise ValueError("Missing whitelisted code: " + case)
    return "\n\n".join(parts), sources, hashes


# Validate the small JSON Schema subset used here; this does not assess claim truth.
def validate_shape(value, schema):
    types = {"object": dict, "array": list, "string": str, "integer": int, "null": type(None)}
    wanted = schema["type"]
    wanted = wanted if isinstance(wanted, list) else [wanted]
    if not any(type(value) is types[kind] for kind in wanted):
        raise ValueError("Wrong JSON field type")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError("Unknown enum value")
    if isinstance(value, dict):
        if set(value) != set(schema["required"]):
            raise ValueError("Missing or additional JSON fields")
        for name, item in value.items():
            validate_shape(item, schema["properties"][name])
    elif isinstance(value, list):
        for item in value:
            validate_shape(item, schema["items"])


# Check types, references and exact quotes against the permitted source map.
# Acceptance means structural/source consistency, never independent factual support.
def validate_claims(value, sources, schema=None):
    if schema is None:
        schema = json.loads((ROOT / "resources/claim_schema.json").read_text(encoding="utf-8"))
    validate_shape(value, schema)
    claims = value["claims"]
    ids = [claim["id"] for claim in claims]
    if any(not item.strip() for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("Empty or duplicate claim ID")
    for claim in claims:
        if not claim["proposition"].strip() or not claim["family_reason"].strip():
            raise ValueError("Empty proposition or family reason")
        if (claim["family"] == "exploitability_impact") != (claim["subtype"] is not None):
            raise ValueError("Family/subtype mismatch")
        if any(ref not in ids or ref == claim["id"] for ref in claim["context_claim_ids"]):
            raise ValueError("Invalid context reference")
        if not claim["evidence"]:
            raise ValueError("Claim without source quote")
        for ref in claim["evidence"]:
            if ref["file"] not in sources:
                raise ValueError("Evidence outside permitted context")
            source = sources[ref["file"]]
            lines = source["text"].splitlines()
            first, last = ref["line_start"], ref["line_end"]
            offset = source["line_start"]
            if not offset <= first <= last < offset + len(lines):
                raise ValueError("Evidence line range outside source")
            excerpt = "\n".join(lines[first - offset:last - offset + 1])
            if not ref["quote"] or ref["quote"] not in excerpt:
                raise ValueError("Evidence quote does not match its lines")
    return {"valid": True, "claim_count": len(claims), "scope": "format, quotes, references; not factuality"}


# Build a new, stateless request; extraction receives only the newly generated report.
def build_request(task, context, prompts, schema, model=MODEL):
    instructions = prompts[task]
    if task != "code_report":
        instructions += "\n\n" + prompts["common_claim_rules"]
    body = {"model": model, "instructions": instructions, "input": context,
            "reasoning": {"effort": "none"}, "store": False, "service_tier": "default",
            "max_output_tokens": REPORT_TOKENS if task == "code_report" else CLAIM_TOKENS}
    if task != "code_report":
        body["text"] = {"format": {"type": "json_schema", "name": "security_claims",
                                     "schema": schema, "strict": True}}
    return body


# Reserve a conservative input-byte/token bound plus the entire output allowance.
# A bounded report size makes preflight finite; each real request is checked again.
def cost_reservation(body):
    size = len(json.dumps(body, ensure_ascii=False).encode("utf-8")) + 2048
    return (size * PRICES["input"] + body["max_output_tokens"] * PRICES["output"]) / 1_000_000


# Prefer process configuration; otherwise read only OPENAI_API_KEY from local .env.
# Never evaluate shell syntax or copy the environment file into research artifacts.
def load_api_key(root=ROOT):
    if os.environ.get("OPENAI_API_KEY", "").strip():
        return os.environ["OPENAI_API_KEY"].strip()
    path = root / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            name, sep, value = line.strip().removeprefix("export ").partition("=")
            if sep and name.strip() == "OPENAI_API_KEY":
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                if value:
                    return value
    raise ValueError("OPENAI_API_KEY fehlt; kein API-Aufruf ausgeführt")


# Perform exactly one HTTPS request; callers save the pending envelope beforehand.
def call_api(body, key):
    request = urllib.request.Request("https://api.openai.com/v1/responses",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"), method="POST",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.loads(response.read())


# Extract completed assistant text; refusals and partial responses remain raw evidence.
def output_text(response):
    if response.get("status") != "completed":
        raise ValueError("Response not completed: " + str(response.get("status")))
    chunks = []
    for item in response.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "refusal":
                    raise ValueError("Model refusal")
                if content.get("type") == "output_text":
                    chunks.append(content["text"])
    text = "".join(chunks)
    if not text.strip():
        raise ValueError("Empty response text")
    return text


# Make report-only numbered input while bounding its maximum serialized preflight size.
def report_context(text):
    lines = text.splitlines()
    if len(text.encode("utf-8")) > REPORT_BYTES or len(lines) > REPORT_LINES:
        raise ValueError("Report exceeds local size bound")
    context = "FILE report.txt\n" + "\n".join(str(i) + " | " + line for i, line in enumerate(lines, 1))
    return context, {"report.txt": {"line_start": 1, "text": text}}


# Run direct first, then report/extraction pairs; preserve invalid outputs without retry.
# Unknown costs or technical failures stop; a bad report blocks only its extraction.
def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "results/run-001")
    parser.add_argument("--budget-usd", type=float, default=1.0)
    parser.add_argument("--model", choices=[MODEL], default=MODEL)
    args = parser.parse_args(argv)
    if not math.isfinite(args.budget_usd) or args.budget_usd <= 0:
        parser.error("--budget-usd must be finite and positive")
    prompts_path, schema_path = ROOT / "resources/prompts.json", ROOT / "resources/claim_schema.json"
    prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    code, baseline_bytes, baseline_hashes = {}, {}, {}
    for case in CASES:
        code[case] = build_code_context(case)
        baseline = ROOT / "examples" / case / "baseline.json"
        baseline_bytes[case] = baseline.read_bytes()
        baseline_hashes[case] = file_hash(baseline)
        validate_claims({"claims": json.loads(baseline_bytes[case])["claims"]}, code[case][1], schema)
    plan = [(case, "code_claims") for case in CASES]
    plan += [(case, task) for case in CASES for task in ("code_report", "report_claims")]
    # Worst permitted serialized report input: escaping plus numbered-line overhead.
    dummy_report = "x" * (REPORT_BYTES * 6 + REPORT_LINES * 16)
    bound = sum(cost_reservation(build_request(task, dummy_report if task == "report_claims"
        else code[case][0], prompts, schema, args.model)) for case, task in plan)
    print(json.dumps({"requests": len(plan), "model": args.model, "max_claim_tokens": CLAIM_TOKENS,
        "max_report_tokens": REPORT_TOKENS, "conservative_cost_bound_usd": round(bound, 6),
        "budget_usd": args.budget_usd, "baseline_hashes": baseline_hashes}, ensure_ascii=False))
    if bound > args.budget_usd:
        raise ValueError("Conservative plan bound exceeds budget; no API request")
    if args.dry_run:
        return 0
    if args.output.exists():
        raise ValueError("Output exists; no overwrite, retry or resume")
    key = load_api_key()
    args.output.mkdir(parents=True, exist_ok=False)
    run = {"created_at": datetime.now(timezone.utc).isoformat(), "status": "running",
        "model": args.model, "reasoning_effort": "none", "budget_usd": args.budget_usd,
        "max_claim_tokens": CLAIM_TOKENS, "max_report_tokens": REPORT_TOKENS,
        "pricing_usd_per_million": PRICES,
        "pricing_source": "https://developers.openai.com/api/docs/pricing",
        "conservative_cost_bound_usd": bound, "planned_requests": len(plan), "spent_estimate_usd": 0.0,
        "reserved_usd": 0.0, "unknown_spend": False, "baseline_hashes": baseline_hashes,
        "code_hashes": {case: code[case][2] for case in CASES},
        "resource_hashes": {p.name: file_hash(p) for p in (prompts_path, schema_path, Path(__file__))},
        "tasks": []}
    for case in CASES:
        directory = args.output / case
        directory.mkdir()
        (directory / "baseline.json").write_bytes(baseline_bytes[case])
    reports = {}
    write_json(args.output / "run.json", run)
    for case, task in plan:
        directory, envelope, row = args.output / case, None, None
        if task == "report_claims" and case not in reports:
            run["tasks"].append({"case": case, "task": task, "status": "blocked",
                "reserved_usd": 0.0, "usage": None, "cost_estimate_usd": 0.0,
                "error": "Report unavailable; no extraction request"})
            write_json(directory / (task + ".json"), {"request": None, "response": None,
                "status": "blocked", "error": "Report unavailable", "validation": None})
            write_json(args.output / "run.json", run)
            continue
        try:
            if file_hash(ROOT / "examples" / case / "baseline.json") != baseline_hashes[case]:
                raise ValueError("Baseline changed after preflight")
            context, sources, hashes = build_code_context(case)
            if hashes != code[case][2]:
                raise ValueError("Code changed after preflight")
            if task == "report_claims":
                context, sources = report_context(reports[case])
            body = build_request(task, context, prompts, schema, args.model)
            reserve = cost_reservation(body)
            if run["spent_estimate_usd"] + run["reserved_usd"] + reserve > args.budget_usd:
                raise ValueError("Request would exceed budget")
            envelope = {"request": body, "response": None, "status": "pending", "error": None, "validation": None}
            row = {"case": case, "task": task, "status": "pending", "reserved_usd": reserve,
                   "usage": None, "cost_estimate_usd": None}
            run["tasks"].append(row)
            run["reserved_usd"] += reserve
            write_json(directory / (task + ".json"), envelope)
            write_json(args.output / "run.json", run)
            response = call_api(body, key)
            envelope["response"] = response
            write_json(directory / (task + ".json"), envelope)
            usage = response.get("usage") or {}
            if any(type(usage.get(name)) is not int or usage[name] < 0 for name in ("input_tokens", "output_tokens")):
                run["unknown_spend"] = True
                raise ValueError("Missing usage; full reservation retained and run stopped")
            cost = (usage["input_tokens"] * PRICES["input"] + usage["output_tokens"] * PRICES["output"]) / 1_000_000
            row.update(usage=usage, cost_estimate_usd=cost)
            run["spent_estimate_usd"] += cost
            run["reserved_usd"] = max(0.0, run["reserved_usd"] - reserve)
            if cost > reserve or run["spent_estimate_usd"] > args.budget_usd:
                raise ValueError("Provider usage exceeded conservative reservation; run stopped")
            try:
                text = output_text(response)
                if task == "code_report":
                    report_context(text)
                    envelope["validation"] = {"valid": True, "word_count": len(text.split())}
                    reports[case] = text
                    (directory / "report.txt").write_text(text, encoding="utf-8")
                else:
                    value = json.loads(text)
                    envelope["validation"] = validate_claims(value, sources, schema)
                    write_json(directory / ("direct.json" if task == "code_claims" else "prose.json"), value)
                envelope["status"] = row["status"] = "completed"
            except ValueError as error:
                envelope["status"] = row["status"] = "invalid_output"
                envelope["error"] = str(error).replace(key, "[REDACTED]")
                envelope["validation"] = {"valid": False, "error": envelope["error"]}
            write_json(directory / (task + ".json"), envelope)
            write_json(args.output / "run.json", run)
            print(case + " " + task + ": " + envelope["status"])
        except Exception as error:
            message = ("HTTP " + str(error.code) if isinstance(error, urllib.error.HTTPError)
                       else str(error) if isinstance(error, ValueError) else type(error).__name__)
            message = message.replace(key, "[REDACTED]")
            if envelope is not None:
                envelope.update(status="error", error=message)
                row["status"] = "error"
                if row["usage"] is None:
                    run["unknown_spend"] = True
                write_json(directory / (task + ".json"), envelope)
            run.update(status="error", error=message)
            write_json(args.output / "run.json", run)
            print("Run stopped: " + message, file=sys.stderr)
            return 1
    run["status"] = ("completed" if all(row["status"] == "completed" for row in run["tasks"])
                     else "completed_with_invalid_outputs")
    write_json(args.output / "run.json", run)
    return 0 if run["status"] == "completed" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as error:
        print("Run not started: " + str(error), file=sys.stderr)
        sys.exit(1)
