"""Synthetic offline fixtures, not empirical security findings."""

import hashlib
from importlib import import_module
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
generator = import_module("02_generate_findings")
MODEL_FILES = generator.MODEL_FILES


def response_bytes(findings):
    return json.dumps({
        "id": "synthetic-generation",
        "model": "synthetic-model",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        "choices": [{
            "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({"findings": findings})},
        }],
    }).encode()


class GenerateFindingsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.dotenv = self.root / ".env"
        dotenv_patch = patch.object(generator, "DOTENV", self.dotenv)
        dotenv_patch.start()
        self.addCleanup(dotenv_patch.stop)
        self.model_input = self.root / "model_input"
        self.output = self.root / "run"
        self.source = "// synthetic fixture\r\n// könnte gelten\r\n".encode()
        for name in MODEL_FILES:
            path = self.model_input / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.source)

    def run_review(self):
        return generator.generate_findings(self.model_input, self.output, "synthetic-model", 100)

    def manifest(self):
        return json.loads((self.output / "run_manifest.json").read_bytes())

    @patch.dict("os.environ", {"OPENAI_API_KEY": "synthetic-test-key"})
    def test_only_allowlisted_sources_sent_and_artifacts_preserved(self):
        marker = "REFERENCE_MUST_NOT_LEAK"
        (self.root / "reference").mkdir()
        (self.root / "reference/fix.txt").write_text(marker)
        (self.root / "manifest.json").write_text(marker)
        (self.model_input / "unexpected.txt").write_text(marker)
        finding = {"title": " Synthetic title ", "report": "Could occur, if enabled.\nUnverified."}
        raw = response_bytes([finding]) + b"\n "
        with patch.object(generator, "request_review", return_value=(200, "test-request", raw)) as request:
            self.assertEqual(self.run_review(), "completed")
        request.assert_called_once()
        sent = request.call_args.args[0]
        self.assertEqual(sent, (self.output / "request.json").read_bytes())
        self.assertNotIn(marker, sent.decode())
        self.assertNotIn("VUL4J-18", sent.decode())
        self.assertNotIn("synthetic-test-key", sent.decode())
        payload = json.loads(sent)
        self.assertNotIn("tools", payload)
        self.assertEqual(payload["model"], "synthetic-model")
        self.assertNotIn("provider", payload)
        self.assertNotIn("plugins", payload)
        self.assertFalse(payload["store"])
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(payload["max_completion_tokens"], 100)
        self.assertNotIn("models", payload)
        self.assertNotIn("reasoning_effort", payload)
        self.assertNotIn("reasoning", payload)
        self.assertNotIn("max_tokens", payload)
        self.assertEqual(len(payload["messages"]), 2)
        self.assertEqual(payload["messages"][0], {
            "role": "system", "content": generator.PROMPT.read_bytes().decode("utf-8"),
        })
        self.assertEqual(payload["messages"][1]["content"].count("FILE: "), 5)
        self.assertIn("1: // synthetic fixture\r\n2: // könnte gelten\r\n", payload["messages"][1]["content"])
        self.assertEqual((self.output / "generation_raw.json").read_bytes(), raw)
        manifest = self.manifest()
        self.assertEqual(manifest["request_sha256"], hashlib.sha256(sent).hexdigest())
        self.assertEqual(manifest["response_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(manifest["usage"]["total_tokens"], 30)
        self.assertEqual(manifest["provider"], "openai")
        self.assertEqual(manifest["endpoint"], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(manifest["response_id"], "synthetic-generation")
        self.assertEqual(manifest["model_returned"], "synthetic-model")
        self.assertEqual(manifest["finish_reason"], "stop")
        self.assertIsNone(manifest["cost_usd"])
        for name in MODEL_FILES:
            self.assertEqual((self.output / "model_input" / name).read_bytes(), self.source)
            self.assertEqual(manifest["source_sha256"][name], hashlib.sha256(self.source).hexdigest())
        saved = json.loads((self.output / "findings.jsonl").read_text())
        self.assertEqual(saved, {"finding_id": f"{manifest['run_id']}:F001", **finding})

    @patch.dict("os.environ", {"OPENAI_API_KEY": "synthetic-test-key"})
    def test_empty_result_is_saved_without_retry(self):
        with patch.object(generator, "request_review", return_value=(200, None, response_bytes([]))) as request:
            self.assertEqual(self.run_review(), "no_findings")
        request.assert_called_once()
        self.assertEqual((self.output / "findings.jsonl").read_bytes(), b"")
        self.assertEqual(self.manifest()["finding_count"], 0)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "synthetic-test-key"})
    def test_invalid_and_incomplete_outputs_are_kept_without_findings(self):
        examples = [b"not JSON", b"[]", b'{"choices": []}', b'{"choices": null}',
                    response_bytes([{"title": "missing report"}])]
        for reason in ["length", "content_filter", "tool_calls", "error", None]:
            response = json.loads(response_bytes([]))
            response["choices"][0]["finish_reason"] = reason
            examples.append(json.dumps(response).encode())
        for field, value in [("refusal", "synthetic refusal"), ("tool_calls", [{}]),
                             ("content", None), ("role", "user")]:
            response = json.loads(response_bytes([]))
            response["choices"][0]["message"][field] = value
            examples.append(json.dumps(response).encode())
        response = json.loads(response_bytes([]))
        response["choices"] *= 2
        examples.append(json.dumps(response).encode())
        for index, raw in enumerate(examples):
            with self.subTest(index=index):
                self.output = self.root / f"invalid-{index}"
                with patch.object(generator, "request_review", return_value=(200, None, raw)) as request:
                    self.assertEqual(self.run_review(), "invalid_output")
                request.assert_called_once()
                self.assertEqual((self.output / "generation_raw.json").read_bytes(), raw)
                self.assertFalse((self.output / "findings.jsonl").exists())
                self.assertEqual(self.manifest()["status"], "invalid_output")

    @patch.dict("os.environ", {"OPENAI_API_KEY": "synthetic-test-key"})
    def test_http_error_and_network_failure_are_saved_without_retry(self):
        raw = b'{"error": "synthetic rate limit"}'
        error = HTTPError(generator.ENDPOINT, 429, "rate limit", {"x-request-id": "err-1"}, io.BytesIO(raw))
        with patch.object(generator, "urlopen", side_effect=error) as request:
            self.assertEqual(self.run_review(), "run_error")
        request.assert_called_once()
        http_request = request.call_args.args[0]
        self.assertEqual(http_request.full_url, "https://api.openai.com/v1/chat/completions")
        self.assertEqual(http_request.get_header("Authorization"), "Bearer synthetic-test-key")
        self.assertEqual(http_request.data, (self.output / "request.json").read_bytes())
        self.assertEqual(self.manifest()["http_status"], 429)
        self.assertEqual((self.output / "generation_raw.json").read_bytes(), raw)
        self.assertFalse((self.output / "findings.jsonl").exists())
        self.output = self.root / "network-error"
        with patch.object(generator, "urlopen", side_effect=URLError("synthetic offline")) as request:
            self.assertEqual(self.run_review(), "run_error")
        request.assert_called_once()
        self.assertEqual(self.manifest()["request_attempts"], 1)
        self.assertFalse((self.output / "generation_raw.json").exists())

        self.output = self.root / "provider-error"
        with patch.object(generator, "request_review", return_value=(200, None, raw)) as request:
            self.assertEqual(self.run_review(), "run_error")
        request.assert_called_once()
        self.assertEqual((self.output / "generation_raw.json").read_bytes(), raw)
        self.assertFalse((self.output / "findings.jsonl").exists())

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_key_is_recorded_without_request(self):
        with patch.object(generator, "request_review") as request:
            self.assertEqual(self.run_review(), "run_error")
        request.assert_not_called()
        self.assertEqual(self.manifest()["request_attempts"], 0)
        self.assertTrue((self.output / "request.json").exists())

    @patch.dict("os.environ", {}, clear=True)
    def test_dotenv_key_is_used_without_entering_saved_artifacts(self):
        key = "synthetic-dotenv-key=secret"
        for index, value in enumerate([key, '"' + key + '"', "'" + key + "'"]):
            with self.subTest(value_format=index):
                self.output = self.root / f"dotenv-{index}"
                self.dotenv.write_text(
                    "# local credentials\n\nUNRELATED=ignored\nOPENAI_API_KEY = " + value + "\n",
                    encoding="utf-8-sig",
                )
                with patch.object(generator, "request_review", return_value=(200, None, response_bytes([]))) as request:
                    self.assertEqual(self.run_review(), "no_findings")
                request.assert_called_once()
                self.assertEqual(request.call_args.args[1], key)
                self.assertNotIn("OPENAI_API_KEY", os.environ)
                for artifact in self.output.rglob("*"):
                    if artifact.is_file():
                        self.assertNotIn(key.encode(), artifact.read_bytes())

    @patch.dict("os.environ", {"OPENAI_API_KEY": "synthetic-environment-key"}, clear=True)
    def test_environment_key_takes_precedence_over_dotenv(self):
        self.dotenv.write_text('OPENAI_API_KEY="unclosed', encoding="utf-8")
        with patch.object(generator, "request_review", return_value=(200, None, response_bytes([]))) as request:
            self.assertEqual(self.run_review(), "no_findings")
        self.assertEqual(request.call_args.args[1], "synthetic-environment-key")

    @patch.dict("os.environ", {}, clear=True)
    def test_empty_or_invalid_dotenv_is_saved_as_error_without_leaking_key(self):
        examples = [b"OPENAI_API_KEY=\n", b"# no key\n",
                    b'OPENAI_API_KEY="synthetic-private-value\n', b"\xff"]
        for index, content in enumerate(examples):
            with self.subTest(index=index):
                self.output = self.root / f"dotenv-error-{index}"
                self.dotenv.write_bytes(content)
                with patch.object(generator, "request_review") as request:
                    self.assertEqual(self.run_review(), "run_error")
                request.assert_not_called()
                self.assertEqual(self.manifest()["request_attempts"], 0)
                self.assertNotIn("synthetic-private-value", self.manifest()["error"])
                self.assertFalse((self.output / "findings.jsonl").exists())

    @patch.dict("os.environ", {"OPENAI_API_KEY": "synthetic-test-key"})
    def test_disabling_reasoning_is_explicit_and_recorded(self):
        with patch.object(generator, "request_review", return_value=(200, None, response_bytes([]))) as request:
            status = generator.generate_findings(
                self.model_input, self.output, "synthetic-model", 8192, disable_reasoning=True,
            )
        self.assertEqual(status, "no_findings")
        request.assert_called_once()
        payload = json.loads(request.call_args.args[0])
        self.assertEqual(payload["reasoning_effort"], "none")
        self.assertEqual(payload["max_completion_tokens"], 8192)
        self.assertEqual(self.manifest()["parameters"]["reasoning_effort"], "none")
        self.assertEqual(request.call_args.args[0], (self.output / "request.json").read_bytes())

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "old-provider-key"}, clear=True)
    def test_old_provider_key_is_not_used_for_openai(self):
        self.dotenv.write_text("OPENROUTER_API_KEY=old-dotenv-key\n", encoding="utf-8")
        with patch.object(generator, "request_review") as request:
            self.assertEqual(self.run_review(), "run_error")
        request.assert_not_called()
        self.assertEqual(self.manifest()["request_attempts"], 0)
        self.assertIn("OPENAI_API_KEY", self.manifest()["error"])
        for path in self.output.rglob("*"):
            if path.is_file():
                self.assertNotIn(b"old-provider-key", path.read_bytes())
                self.assertNotIn(b"old-dotenv-key", path.read_bytes())

    def test_invalid_or_openrouter_models_are_rejected_before_creating_run(self):
        for model in ["nvidia/model:free", "openrouter/free", "", "model:free", "synthetic-model "]:
            with self.subTest(model=model):
                with patch.object(generator, "request_review") as request:
                    with self.assertRaises(ValueError):
                        generator.generate_findings(self.model_input, self.output, model, 100)
                request.assert_not_called()
                self.assertFalse(self.output.exists())

    def test_existing_run_is_not_touched(self):
        self.output.mkdir()
        marker = self.output / "keep.txt"
        marker.write_text("existing run")
        with patch.object(generator, "request_review") as request:
            with self.assertRaises(FileExistsError):
                self.run_review()
        request.assert_not_called()
        self.assertEqual(marker.read_text(), "existing run")

    def test_symlink_cannot_import_reference_material(self):
        source = self.model_input / MODEL_FILES[0]
        source.unlink()
        reference = self.root / "reference.txt"
        reference.write_text("reference only")
        try:
            source.symlink_to(reference)
        except OSError as error:
            if getattr(error, "winerror", None) == 1314:
                self.skipTest("Windows symlink privilege is unavailable.")
            raise
        with patch.object(generator, "request_review") as request:
            with self.assertRaises(ValueError):
                self.run_review()
        request.assert_not_called()
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
