"""Save one tool-free review through an explicitly selected OpenAI model."""

import argparse
from datetime import datetime, timezone
import hashlib
from importlib import import_module
from http.client import HTTPException
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

# Numbered pipeline scripts are loaded by name because Python import syntax
# does not allow identifiers starting with digits.
prepare_case = import_module("01_prepare_case")
CASE_ID = prepare_case.CASE_ID
MODEL_FILES = prepare_case.MODEL_FILES
json_bytes = prepare_case.json_bytes


ENDPOINT = "https://api.openai.com/v1/chat/completions"
DOTENV = Path(__file__).resolve().parents[1] / ".env"
PROMPT = Path(__file__).resolve().parents[1] / "resources" / "review_prompt.txt"
TIMEOUT_SECONDS = 180


# Berechnet den SHA-256-Hash der übergebenen Originalbytes als Hex-String.
# Dient zur Zuordnung und späteren Integritätsprüfung der gespeicherten Artefakte.
def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# Liest den API-Key zuerst aus der Prozessumgebung, danach aus der Projekt-.env.
# Unterstützt einen einfachen, optional zitierten Eintrag; fehlender Key ergibt einen leeren String.
# Verändert die Umgebung nicht und nimmt den Schlüssel nicht in Fehlermeldungen auf.
def load_api_key() -> str:
    """Read the environment first, then the project's simple .env key entry."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    try:
        lines = DOTENV.read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        return ""
    except UnicodeError:
        raise ValueError("The project .env must be UTF-8 encoded.") from None
    for line in lines:
        name, separator, value = line.partition("=")
        if name.strip() != "OPENAI_API_KEY" or not separator:
            continue
        value = value.strip()
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError("OPENAI_API_KEY in .env has unmatched quotes.")
            value = value[1:-1]
        return value
    return ""


# Liest ausschließlich die fünf erlaubten Dateien als Pfad-zu-Bytes-Dictionary.
# Lehnt Symlinks am Eingabeverzeichnis und innerhalb der Dateipfade ab, um Referenzzugriffe zu verhindern.
def load_sources(model_input: Path) -> dict:
    """Read only the allowlist; reject symlinks that could expose references."""
    if model_input.is_symlink():
        raise ValueError(f"Model input must not be a symlink: {model_input}")
    files = {}
    for name in MODEL_FILES:
        source = model_input
        for part in Path(name).parts:
            source = source / part
            if source.is_symlink():
                raise ValueError(f"Symlinks are not allowed in model input: {source}")
        files[name] = source.read_bytes()
    return files


# Sendet den vorbereiteten Request einmal an OpenAI; der Key steht nur im HTTP-Header.
# Gibt HTTP-Status, Request-ID und rohe Antwortbytes zurück, auch bei HTTP-Fehlern.
# Wiederholt den Aufruf nicht; Netzwerkfehler werden an den Aufrufer weitergegeben.
def request_review(body: bytes, api_key: str) -> tuple:
    """One HTTP request, with no automatic retries or agent tools."""
    request = Request(ENDPOINT, data=body, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, response.headers.get("x-request-id"), response.read()
    except HTTPError as error:
        return error.code, error.headers.get("x-request-id"), error.read()


# Prüft eine vollständig beendete Antwort und das JSON-Format der Findings.
# Gibt Titel und Reports unverändert zurück; lehnt Abbrüche, Refusals und Toolaufrufe ab.
# Prüft nur die Struktur, nicht den Wahrheitsgehalt der Sicherheitsbehauptungen.
def parse_findings(response: dict) -> list:
    """Check the report envelope, without repairing or verifying its claims."""
    choices = response["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("Expected exactly one completion.")
    choice = choices[0]
    if choice.get("finish_reason") == "length":
        raise ValueError("Output token limit reached (finish_reason=length); response is incomplete.")
    if choice.get("error") or choice.get("finish_reason") != "stop":
        raise ValueError(f"Completion did not finish normally: {choice.get('finish_reason')}")
    message = choice["message"]
    if (message.get("role") != "assistant" or message.get("refusal")
            or message.get("tool_calls") or not isinstance(message.get("content"), str)):
        raise ValueError("Refusal, tool call or non-text output; not an empty finding list.")
    report = json.loads(message["content"])
    if not isinstance(report, dict) or set(report) != {"findings"}:
        raise ValueError("Expected exactly one findings field.")
    findings = report["findings"]
    if not isinstance(findings, list):
        raise ValueError("findings must be a list.")
    for finding in findings:
        if not isinstance(finding, dict) or set(finding) != {"title", "report"}:
            raise ValueError("Each finding must contain exactly title and report.")
        if any(not isinstance(value, str) or not value.strip() for value in finding.values()):
            raise ValueError("Finding title and report must be nonempty strings.")
    return findings


# Erstellt aus dem erlaubten Quellkontext einen einzelnen Review-Lauf für ein explizit gewähltes OpenAI-Modell.
# Speichert Eingaben, Request, erhaltene Rohantwort und gültige Findings in einem neuen Laufverzeichnis.
# Hält auch leere Ergebnisse und Fehler im Manifest fest und gibt den Laufstatus zurück.
# Optional setzt --no-reasoning reasoning_effort=none; das Modell muss diesen Wert unterstützen.
def generate_findings(model_input: Path, output: Path, model: str,
                      max_output_tokens: int, disable_reasoning: bool = False) -> str:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Output already exists: {output}. Choose a new --output path.")
    if not model or "/" in model or model.endswith(":free") or any(char.isspace() for char in model):
        raise ValueError("Select an explicit OpenAI model ID (without an OpenRouter prefix or :free suffix).")
    if max_output_tokens < 1:
        raise ValueError("A positive max-output-tokens value is required.")

    files = load_sources(model_input)
    prompt = PROMPT.read_bytes()
    sections = []
    for name, content in files.items():
        lines = content.decode("utf-8").splitlines(keepends=True)
        numbered = "".join(f"{number}: {line}" for number, line in enumerate(lines, 1))
        sections.append(f"FILE: {name}\n{numbered}\nEND FILE\n")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt.decode("utf-8")},
            {"role": "user", "content": "\n".join(sections)},
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
        "case_id": CASE_ID,
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "provider": "openai",
        "endpoint": ENDPOINT,
        "model_requested": model,
        "parameters": {key: value for key, value in payload.items()
                       if key != "messages"},
        "prompt_file": PROMPT.name,
        "prompt_sha256": sha256(prompt),
        "request_sha256": sha256(body),
        "source_sha256": {name: sha256(content) for name, content in files.items()},
        "generator_sha256": sha256(Path(__file__).read_bytes()),
        "timeout_seconds": TIMEOUT_SECONDS,
        "request_attempts": 0,
        "status": "running",
        "usage": None,
        "cost_usd": None,
    }

    # Reserve a new directory. Preserve every started run, including failures.
    output.mkdir(parents=True)
    for name, content in files.items():
        target = output / "model_input" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    (output / PROMPT.name).write_bytes(prompt)
    (output / "request.json").write_bytes(body)
    (output / "run_manifest.json").write_bytes(json_bytes(manifest))

    started = time.monotonic()
    try:
        api_key = load_api_key()
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing from the environment and project .env; no request was sent.")
        manifest["request_attempts"] = 1
        (output / "run_manifest.json").write_bytes(json_bytes(manifest))
        status, request_id, raw = request_review(body, api_key)
        (output / "generation_raw.json").write_bytes(raw)
        manifest.update(http_status=status, provider_request_id=request_id,
                        response_sha256=sha256(raw))
        if status != 200:
            raise ValueError(f"Provider HTTP status {status}; see generation_raw.json.")
    except (OSError, URLError, HTTPException, ValueError) as error:
        manifest.update(status="run_error", error=f"{type(error).__name__}: {error}")
    else:
        try:
            response = json.loads(raw)
            manifest.update(model_returned=response.get("model"),
                            usage=response.get("usage"),
                            response_id=response.get("id"),
                            system_fingerprint=response.get("system_fingerprint"))
            if response.get("error"):
                raise RuntimeError("Provider reported an error; see generation_raw.json.")
            findings = parse_findings(response)
            manifest["finish_reason"] = response["choices"][0]["finish_reason"]
            rows = [json.dumps({"finding_id": f"{run_id}:F{index:03d}", **finding},
                               ensure_ascii=False) + "\n"
                    for index, finding in enumerate(findings, 1)]
            findings_file = output / "findings.jsonl.tmp"
            findings_file.write_bytes("".join(rows).encode("utf-8"))
            findings_file.rename(output / "findings.jsonl")
            manifest.update(status="completed" if findings else "no_findings",
                            finding_count=len(findings))
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            manifest.update(status="invalid_output", error=f"{type(error).__name__}: {error}")
        except (OSError, RuntimeError) as error:
            manifest.update(status="run_error", error=f"{type(error).__name__}: {error}")
    finally:
        if manifest["status"] == "running":
            manifest.update(status="run_error", error="Review interrupted before completion.")
        manifest["duration_seconds"] = round(time.monotonic() - started, 3)
        manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
        (output / "run_manifest.json").write_bytes(json_bytes(manifest))
    return manifest["status"]


# Liest CLI-Parameter für Modellkontext, Laufverzeichnis, Tokenlimit und optionales Abschalten von Reasoning.
# Startet den Generator und meldet Startfehler oder gespeicherte Laufursachen mit Exit-Code 1.
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-input", type=Path, default=Path("data") / CASE_ID / "model_input")
    parser.add_argument("--output", type=Path, required=True, help="New run directory under data/.")
    parser.add_argument("--model", required=True,
                        help="Explicit OpenAI model ID; no default or automatic model selection.")
    parser.add_argument("--max-output-tokens", type=int, required=True,
                        help="Output limit including reasoning; not a monetary budget.")
    parser.add_argument("--no-reasoning", action="store_true",
                        help="Send reasoning_effort=none; requires a model supporting none. Omit for model defaults.")
    args = parser.parse_args()
    try:
        status = generate_findings(args.model_input, args.output, args.model,
                                   args.max_output_tokens, disable_reasoning=args.no_reasoning)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Could not start review: {error}\n")
    print(f"Review status: {status}; saved at {args.output.resolve()}")
    if status not in ("completed", "no_findings"):
        manifest = json.loads((args.output / "run_manifest.json").read_bytes())
        parser.exit(1, f"Review did not complete: {manifest.get('error', status)}\n"
                       "See run_manifest.json. No automatic retry.\n")


if __name__ == "__main__":
    main()
