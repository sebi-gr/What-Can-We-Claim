"""Decompose one saved finding with the claim codebook and validate its claim format."""

import argparse
from datetime import datetime, timezone
from importlib import import_module
from http.client import HTTPException
import json
from pathlib import Path
import re
import time
from uuid import uuid4

generator = import_module("02_generate_findings")
json_bytes = generator.json_bytes
sha256 = generator.sha256
RESOURCES = Path(__file__).resolve().parents[1] / "resources"
PROMPT = RESOURCES / "decomposition_prompt.txt"
CODEBOOK = RESOURCES / "claim_codebook.md"
SCHEMA = RESOURCES / "claim_response_schema.json"
SCHEMA_VERSION = "1"
FAMILIES = ("location", "data_flow", "protection_precondition",
            "exploitability_impact", "other", "unclear")
CLAIM_FIELDS = {"claim_id", "proposition", "family", "subtype", "family_reason",
                "source_quotes", "qualifiers", "context_claim_ids"}
CLAIM_ID = re.compile(r"C[0-9]{2,}[a-z]?")


# Übernimmt JSON-Objektpaare ohne doppelte Schlüssel; verhindert stilles Überschreiben.
# Wird beim Laden von Finding- und Modell-JSON verwendet, ohne Inhalte zu korrigieren.
def unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key.")
        result[key] = value
    return result


# Prüft die exakt erlaubten Objektfelder; unbekannte Felder sind kein stiller Zusatz.
# Benennt fehlende und zusätzliche Felder; verändert oder repariert die Eingabe nicht.
def require_keys(value: object, expected: set, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label}: expected a JSON object.")
    differences = []
    missing = sorted(expected - set(value))
    unexpected = sorted(set(value) - expected)
    if missing:
        differences.append(f"missing fields {json.dumps(missing)}")
    if unexpected:
        differences.append(f"unexpected fields {json.dumps(unexpected)}")
    if differences:
        raise ValueError(f"{label}: {'; '.join(differences)}.")


# Prüft nichtleere Texte, ohne Leerzeichen oder Formulierungen zu verändern.
# Der Feldname dient nur zur verständlichen Fehlermeldung.
def require_text(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: expected nonempty text.")


# Lädt genau die explizite JSONL-Datei und wählt eine eindeutige Finding-ID.
# Verlangt Generatorfelder, lehnt Symlink-Pfade/doppelte IDs ab und liest keine Nachbardateien.
# Liefert die Originalbytes der Datei sowie das ausgewählte Finding zurück.
def load_finding(path: Path, finding_id: str) -> tuple:
    absolute = path.absolute()
    if any(part.is_symlink() for part in (absolute, *absolute.parents)):
        raise ValueError("Finding input must not use symlinks.")
    raw = path.read_bytes()
    selected = None
    ids = set()
    for number, line in enumerate(raw.decode("utf-8").split("\n"), 1):
        if not line.strip():
            continue
        finding = json.loads(line, object_pairs_hook=unique_object)
        require_keys(finding, {"finding_id", "title", "report"}, f"Input line {number}")
        for key, value in finding.items():
            require_text(value, f"Input line {number}.{key}")
        if finding["finding_id"] in ids:
            raise ValueError("Duplicate finding_id in input.")
        ids.add(finding["finding_id"])
        if finding["finding_id"] == finding_id:
            selected = finding
    if selected is None:
        raise ValueError("Selected finding_id was not found; no request sent.")
    return raw, selected


# Akzeptiert nur eine regulär beendete Textantwort ohne Refusal oder Toolaufrufe.
# Dekodiert deren JSON, ohne abgebrochene Antworten zu reparieren oder Reasoning zu übernehmen.
def parse_response(response: dict) -> dict:
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        raise ValueError("Expected exactly one completion.")
    choice = choices[0]
    if choice.get("finish_reason") == "length":
        raise ValueError("Output token limit reached (finish_reason=length); response is incomplete.")
    if choice.get("error") or choice.get("finish_reason") != "stop":
        raise ValueError("Completion did not finish normally.")
    message = choice.get("message")
    if (not isinstance(message, dict) or message.get("role") != "assistant"
            or message.get("refusal") or message.get("tool_calls")
            or not isinstance(message.get("content"), str)):
        raise ValueError("Refusal, tool call or non-text output; not an empty claim list.")
    return json.loads(message["content"], object_pairs_hook=unique_object)


# Prüft den festen v1-Vertrag, IDs, Familien, Zitate und Kontextreferenzen.
# Berechnet Zitat-Offsets in nullbasierten Unicode-Codepoints (Ende exklusiv), ohne Normalisierung.
# Liefert neue Claim-Dictionaries; Bedeutungstreue, Vollständigkeit und Wahrheit werden nicht geprüft.
def validate_claims(document: dict, finding: dict) -> list:
    require_keys(document, {"schema_version", "claims"}, "Response")
    if document["schema_version"] != SCHEMA_VERSION or not isinstance(document["claims"], list):
        raise ValueError("Expected schema_version '1' and a claims list.")
    result = []
    ids = set()
    for index, claim in enumerate(document["claims"]):
        label = f"claims[{index}]"
        require_keys(claim, CLAIM_FIELDS, label)
        for key in ("claim_id", "proposition", "family", "family_reason", "qualifiers"):
            require_text(claim[key], f"{label}.{key}")
        if not CLAIM_ID.fullmatch(claim["claim_id"]) or claim["claim_id"] in ids:
            raise ValueError(f"{label}: invalid or duplicate claim_id.")
        ids.add(claim["claim_id"])
        if claim["family"] not in FAMILIES:
            raise ValueError(f"{label}: unknown family.")
        if claim["family"] == "exploitability_impact":
            if claim["subtype"] not in ("exploitability", "impact", "unclear"):
                raise ValueError(f"{label}: exploitability_impact requires a subtype.")
        elif claim["subtype"] is not None:
            raise ValueError(f"{label}: subtype must be null for this family.")
        references = claim["context_claim_ids"]
        if not isinstance(references, list):
            raise ValueError(f"{label}: context_claim_ids must be a list.")
        for reference in references:
            if not isinstance(reference, str) or not CLAIM_ID.fullmatch(reference):
                raise ValueError(f"{label}: invalid context claim ID.")
        if len(set(references)) != len(references) or claim["claim_id"] in references:
            raise ValueError(f"{label}: duplicate or self context reference.")
        quotes = claim["source_quotes"]
        if not isinstance(quotes, list) or not quotes:
            raise ValueError(f"{label}: source_quotes must be a nonempty list.")
        resolved = []
        seen_quotes = set()
        for quote in quotes:
            require_keys(quote, {"field", "quote", "occurrence"}, f"{label}.source_quotes")
            if quote["field"] not in ("title", "report"):
                raise ValueError(f"{label}: quote field must be title or report.")
            require_text(quote["quote"], f"{label}.quote")
            occurrence = quote["occurrence"]
            if type(occurrence) is not int or occurrence < 1:
                raise ValueError(f"{label}: quote occurrence must be a positive integer.")
            identity = (quote["field"], quote["quote"], occurrence)
            if identity in seen_quotes:
                raise ValueError(f"{label}: duplicate source quote.")
            seen_quotes.add(identity)
            source = finding[quote["field"]]
            start = -1
            for _ in range(occurrence):
                start = source.find(quote["quote"], start + 1)
                if start < 0:
                    raise ValueError(f"{label}: exact quote occurrence not found in {quote['field']}.")
            resolved.append({**quote, "start": start, "end": start + len(quote["quote"])})
        result.append({**claim, "source_quotes": resolved})
    for claim in result:
        if any(reference not in ids for reference in claim["context_claim_ids"]):
            raise ValueError(f"{claim['claim_id']}: unresolved context claim ID.")
    return result


# Zerlegt ein ausgewähltes Finding in einem neuen Laufverzeichnis mit einem OpenAI-Modell.
# Speichert Originaleingabe, Codebook/Prompt/Schema, Request, Rohantwort, Validierung und gültige Claims.
# Nutzt nur Key-Lader/HTTP-Aufruf/Serialisierung des Generators; kein Quellcode- oder Referenzzugriff.
# Kein Retry/Repair; bei Fehlern bleiben Artefakte erhalten, ohne partielle gültige Claims auszugeben.
def decompose_findings(findings_path: Path, finding_id: str, output: Path, model: str,
                       max_output_tokens: int, disable_reasoning: bool = False) -> str:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Output already exists: {output}. Choose a new --output path.")
    if not model or "/" in model or model.endswith(":free") or any(char.isspace() for char in model):
        raise ValueError("Select an explicit OpenAI model ID (without an OpenRouter prefix or :free suffix).")
    if max_output_tokens < 1:
        raise ValueError("A positive max-output-tokens value is required.")
    input_bytes, finding = load_finding(findings_path, finding_id)
    resources = {path.name: path.read_bytes() for path in (PROMPT, CODEBOOK, SCHEMA)}
    system = (resources[PROMPT.name].decode("utf-8")
              + "\n\nCODEBOOK\n" + resources[CODEBOOK.name].decode("utf-8")
              + "\n\nRESPONSE SCHEMA\n" + resources[SCHEMA.name].decode("utf-8"))
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(
                {key: finding[key] for key in ("title", "report")}, ensure_ascii=False)},
        ],
        "max_completion_tokens": max_output_tokens,
        "stream": False,
        "store": False,
        "response_format": {"type": "json_object"},
    }
    if disable_reasoning:
        payload["reasoning_effort"] = "none"
    body = json_bytes(payload)
    run_id = str(uuid4())
    manifest = {
        "run_id": run_id, "finding_id": finding_id, "schema_version": SCHEMA_VERSION,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "provider": "openai", "endpoint": generator.ENDPOINT,
        "model_requested": model,
        "parameters": {key: value for key, value in payload.items() if key != "messages"},
        "findings_input_sha256": sha256(input_bytes),
        "finding_sha256": sha256(json_bytes(finding)),
        "resource_sha256": {name: sha256(content) for name, content in resources.items()},
        "implementation_sha256": {
            path.name: sha256(path.read_bytes()) for path in (
                Path(__file__), Path(generator.__file__), Path(generator.prepare_case.__file__))},
        "request_sha256": sha256(body), "timeout_seconds": generator.TIMEOUT_SECONDS,
        "request_attempts": 0, "status": "running", "usage": None, "cost_usd": None,
    }
    validation = {"status": "not_run", "claim_count": None, "errors": [],
                  "scope": "Format, exact quotes and references; not semantic correctness or truth."}
    output.mkdir(parents=True)
    (output / "run_manifest.json").write_bytes(json_bytes(manifest))
    started = time.monotonic()
    phase = "setup"
    try:
        for name, content in resources.items():
            (output / name).write_bytes(content)
        (output / "findings_input.jsonl").write_bytes(input_bytes)
        (output / "finding.json").write_bytes(json_bytes(finding))
        (output / "request.json").write_bytes(body)
        api_key = generator.load_api_key()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing from the environment and project .env.")
        phase = "request"
        manifest["request_attempts"] = 1
        (output / "run_manifest.json").write_bytes(json_bytes(manifest))
        status, request_id, raw = generator.request_review(body, api_key)
        (output / "decomposition_raw.json").write_bytes(raw)
        manifest.update(http_status=status, provider_request_id=request_id, response_sha256=sha256(raw))
        if status != 200:
            raise RuntimeError(f"Provider HTTP status {status}; see decomposition_raw.json.")
        phase = "response"
        response = json.loads(raw, object_pairs_hook=unique_object)
        if not isinstance(response, dict):
            raise ValueError("Provider response must be a JSON object.")
        manifest.update(model_returned=response.get("model"), usage=response.get("usage"),
                        response_id=response.get("id"),
                        system_fingerprint=response.get("system_fingerprint"))
        if response.get("error"):
            raise RuntimeError("Provider reported an error; see decomposition_raw.json.")
        document = parse_response(response)
        manifest["finish_reason"] = "stop"
        claims = validate_claims(document, finding)
        validation.update(status="passed", claim_count=len(claims))
        phase = "save"
        rows = [{"schema_version": SCHEMA_VERSION, "run_id": run_id, "finding_id": finding_id,
                 **claim, "verification_status": "not_evaluated"} for claim in claims]
        temporary = output / "claims.jsonl.tmp"
        temporary.write_bytes("".join(json.dumps(row, ensure_ascii=False) + "\n"
                                      for row in rows).encode("utf-8"))
        temporary.rename(output / "claims.jsonl")
        manifest.update(status="completed" if claims else "no_claims", claim_count=len(claims))
    except (ValueError, TypeError, KeyError) as error:
        status = "invalid_output" if phase == "response" else "run_error"
        manifest.update(status=status, error=f"{type(error).__name__}: {error}")
        if status == "invalid_output":
            validation.update(status="failed", errors=[str(error)])
    except (OSError, HTTPException, RuntimeError) as error:
        manifest.update(status="run_error", error=f"{type(error).__name__}: {error}")
    finally:
        if manifest["status"] == "running":
            manifest.update(status="run_error", error="Decomposition interrupted before completion.")
        manifest.update(duration_seconds=round(time.monotonic() - started, 3),
                        finished_at=datetime.now(timezone.utc).isoformat())
        (output / "validation.json").write_bytes(json_bytes(validation))
        (output / "run_manifest.json").write_bytes(json_bytes(manifest))
    return manifest["status"]


# Liest Finding-Auswahl und explizite Modell-/Budgetparameter und startet einen Lauf.
# Meldet gespeicherte Fehler mit Exit-Code 1; erfolgreich bedeutet nur formal gültige Claims.
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--findings", type=Path, required=True, help="Saved generator findings.jsonl.")
    parser.add_argument("--finding-id", required=True, help="Exactly one finding_id from that file.")
    parser.add_argument("--output", type=Path, required=True, help="New run directory under data/.")
    parser.add_argument("--model", required=True, help="Explicit OpenAI model ID.")
    parser.add_argument("--max-output-tokens", type=int, required=True, help="Output budget including reasoning.")
    parser.add_argument("--no-reasoning", action="store_true", help="Send reasoning_effort=none; requires a model supporting none.")
    args = parser.parse_args()
    try:
        status = decompose_findings(args.findings, args.finding_id, args.output, args.model,
                                    args.max_output_tokens, args.no_reasoning)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Could not start decomposition: {error}\n")
    print(f"Decomposition status: {status}; saved at {args.output.resolve()}")
    if status not in ("completed", "no_claims"):
        manifest = json.loads((args.output / "run_manifest.json").read_bytes())
        parser.exit(1, f"Decomposition did not complete: {manifest.get('error', status)}\n"
                       "See run_manifest.json and validation.json. No automatic retry.\n")


if __name__ == "__main__":
    main()
