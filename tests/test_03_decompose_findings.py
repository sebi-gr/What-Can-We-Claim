"""Offline decomposition checks with synthetic findings and provider responses."""

from copy import deepcopy
from importlib import import_module
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
decomposer = import_module("03_decompose_findings")


def claim_fixture():
    return {
        "claim_id": "C01", "proposition": "A synthetic assertion, possibly conditional.",
        "family": "other", "subtype": None, "family_reason": "Synthetic fixture.",
        "qualifiers": "Possible; condition not specified.",
        "source_quotes": [{"field": "report", "quote": "aba", "occurrence": 2}],
        "context_claim_ids": [],
    }


def response_fixture(claims):
    return {
        "id": "synthetic-response", "model": "test-model",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        "choices": [{"finish_reason": "stop", "message": {
            "role": "assistant", "content": json.dumps({"schema_version": "1", "claims": claims}),
        }}],
    }


class DecomposeFindingsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.finding = {"finding_id": "synthetic:F001", "title": "Synthetic title",
                        "report": "🙂 ababa.\r\nCould occur if enabled; not established."}
        self.input = self.root / "findings.jsonl"
        self.input.write_bytes((json.dumps(self.finding, ensure_ascii=False) + "\r\n").encode())
        self.output = self.root / "run"
        key = patch.object(decomposer.generator, "load_api_key", return_value="synthetic-test-key")
        key.start()
        self.addCleanup(key.stop)

    def run_decomposition(self, **kwargs):
        return decomposer.decompose_findings(self.input, self.finding["finding_id"],
                                            self.output, "test-model", 8192, **kwargs)

    def manifest(self):
        return json.loads((self.output / "run_manifest.json").read_bytes())

    def test_request_isolation_and_reproducible_artifacts(self):
        marker = "REFERENCE_MUST_NOT_BE_SENT"
        for name in ("model_input", "reference", "annotations"):
            (self.root / name).mkdir()
            (self.root / name / "secret.txt").write_text(marker)
        other = {"finding_id": "other", "title": marker, "report": marker}
        self.input.write_bytes(self.input.read_bytes() + (json.dumps(other) + "\n").encode())
        raw = json.dumps(response_fixture([claim_fixture()])).encode() + b"\n "
        with patch.object(decomposer.generator, "request_review", return_value=(200, "request-id", raw)) as request:
            with patch.object(decomposer.generator, "load_sources", side_effect=AssertionError("No code context")):
                self.assertEqual(self.run_decomposition(disable_reasoning=True), "completed")
        request.assert_called_once()
        sent = request.call_args.args[0]
        payload = json.loads(sent)
        self.assertNotIn(marker, sent.decode())
        self.assertNotIn(self.finding["finding_id"], sent.decode())
        self.assertEqual(json.loads(payload["messages"][1]["content"]),
                         {key: self.finding[key] for key in ("title", "report")})
        self.assertIn(decomposer.CODEBOOK.read_text(encoding="utf-8"), payload["messages"][0]["content"])
        self.assertEqual(payload["reasoning_effort"], "none")
        self.assertNotIn("tools", payload)
        self.assertNotIn("provider", payload)
        self.assertNotIn("plugins", payload)
        self.assertFalse(payload["store"])
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(payload["max_completion_tokens"], 8192)
        self.assertEqual((self.output / "request.json").read_bytes(), sent)
        self.assertEqual((self.output / "decomposition_raw.json").read_bytes(), raw)
        self.assertEqual((self.output / "findings_input.jsonl").read_bytes(), self.input.read_bytes())
        manifest = self.manifest()
        self.assertEqual(manifest["request_sha256"], decomposer.sha256(sent))
        self.assertEqual(manifest["response_sha256"], decomposer.sha256(raw))
        self.assertEqual(manifest["provider"], "openai")
        self.assertEqual(manifest["endpoint"], "https://api.openai.com/v1/chat/completions")
        for name, expected in manifest["resource_sha256"].items():
            self.assertEqual(decomposer.sha256((self.output / name).read_bytes()), expected)
        row = json.loads((self.output / "claims.jsonl").read_bytes())
        self.assertEqual(row["proposition"], claim_fixture()["proposition"])
        self.assertEqual(row["finding_id"], self.finding["finding_id"])
        self.assertEqual(row["run_id"], manifest["run_id"])
        self.assertEqual(row["verification_status"], "not_evaluated")
        self.assertEqual(row["source_quotes"][0]["start"], 4)  # codepoints, not UTF-8/UTF-16
        self.assertEqual(row["source_quotes"][0]["end"], 7)
        for path in self.output.iterdir():
            self.assertNotIn(b"synthetic-test-key", path.read_bytes())

    def test_quote_offsets_context_and_no_input_mutation(self):
        first = claim_fixture()
        second = {**deepcopy(first), "claim_id": "C02", "context_claim_ids": ["C01"],
                  "source_quotes": [{"field": "report", "quote": ".\r\nCould", "occurrence": 1}]}
        document = {"schema_version": "1", "claims": [first, second]}
        original = deepcopy(document)
        claims = decomposer.validate_claims(document, self.finding)
        self.assertEqual(document, original)
        for claim in claims:
            for quote in claim["source_quotes"]:
                self.assertEqual(self.finding[quote["field"]][quote["start"]:quote["end"]], quote["quote"])
        self.assertEqual(claims[1]["context_claim_ids"], ["C01"])

    def test_same_sentence_can_support_claims_in_different_families(self):
        sentence = "In Handler.run, request.name is passed to lookup without validation."
        finding = {**self.finding, "report": sentence}
        assertions = [
            ("location", "Handler.run calls lookup."),
            ("data_flow", "request.name is passed to lookup."),
            ("protection_precondition", "request.name is passed to lookup without validation."),
        ]
        claims = [{**claim_fixture(), "claim_id": f"C{index:02d}",
                   "family": family, "proposition": proposition,
                   "source_quotes": [{"field": "report", "quote": sentence, "occurrence": 1}]}
                  for index, (family, proposition) in enumerate(assertions, 1)]
        result = decomposer.validate_claims({"schema_version": "1", "claims": claims}, finding)
        self.assertEqual(len(result), 3)
        for original, resolved in zip(claims, result):
            self.assertEqual(resolved["proposition"], original["proposition"])
            self.assertEqual(resolved["family"], original["family"])
            self.assertEqual(resolved["source_quotes"][0]["start"], 0)
            self.assertEqual(resolved["source_quotes"][0]["end"], len(sentence))

    def test_unicode_separators_inside_report_are_not_jsonl_boundaries(self):
        self.finding["report"] += "\u2028second paragraph\u2029\u0085end"
        raw = (json.dumps(self.finding, ensure_ascii=False) + "\r\n").encode("utf-8")
        self.input.write_bytes(raw)
        saved, selected = decomposer.load_finding(self.input, self.finding["finding_id"])
        self.assertEqual(saved, raw)
        self.assertEqual(selected, self.finding)

    def test_invalid_claim_contract_and_quotes_rejected(self):
        variants = [
            {"proposition": " "}, {"family": "invented"}, {"family_reason": 4},
            {"qualifiers": []}, {"claim_id": "C1"}, {"subtype": "impact"},
            {"family": "exploitability_impact", "subtype": None},
            {"context_claim_ids": ["C01"]}, {"context_claim_ids": ["C02"]},
            {"context_claim_ids": [True]}, {"context_claim_ids": ["C02", "C02"]},
            {"source_quotes": []}, {"source_quotes": "text"},
            {"source_quotes": [{"field": "code", "quote": "aba", "occurrence": 1}]},
            {"source_quotes": [{"field": "report", "quote": "invented", "occurrence": 1}]},
            {"source_quotes": [{"field": "report", "quote": ".\nCould", "occurrence": 1}]},
            {"source_quotes": [{"field": "report", "quote": "aba", "occurrence": 3}]},
            {"source_quotes": [{"field": "report", "quote": "aba", "occurrence": True}]},
            {"source_quotes": [{"field": "report", "quote": "aba", "occurrence": 0}]},
            {"verification_status": "supported"},
        ]
        for variant in variants:
            with self.subTest(variant=variant):
                with self.assertRaises(ValueError):
                    decomposer.validate_claims({"schema_version": "1", "claims": [
                        {**claim_fixture(), **variant}]}, self.finding)
        for document in ([], {"claims": []}, {"schema_version": "2", "claims": []},
                         {"schema_version": "1", "claims": [claim_fixture(), claim_fixture()]}):
            with self.subTest(document=document), self.assertRaises(ValueError):
                decomposer.validate_claims(document, self.finding)

    def test_invalid_output_has_no_partial_claims_or_retry(self):
        good = claim_fixture()
        bad = {**deepcopy(good), "claim_id": "C02", "context_claim_ids": ["C99"]}
        raw = json.dumps(response_fixture([good, bad])).encode()
        with patch.object(decomposer.generator, "request_review", return_value=(200, None, raw)) as request:
            self.assertEqual(self.run_decomposition(), "invalid_output")
        request.assert_called_once()
        self.assertFalse((self.output / "claims.jsonl").exists())
        self.assertEqual((self.output / "decomposition_raw.json").read_bytes(), raw)
        validation = json.loads((self.output / "validation.json").read_bytes())
        self.assertEqual(validation["status"], "failed")
        self.assertIn("unresolved", validation["errors"][0])

    def test_field_errors_name_differences_and_preserve_invalid_response(self):
        extra = {**claim_fixture(), "claim_id": "C03", "possible if enabled": "condition"}
        missing = {key: value for key, value in extra.items()
                   if key not in ("possible if enabled", "subtype")}
        variants = [
            (extra, 'unexpected fields ["possible if enabled"]'),
            (missing, 'missing fields ["subtype"]'),
            ({**missing, "possible if enabled": "condition"},
             'missing fields ["subtype"]; unexpected fields ["possible if enabled"]'),
            (None, 'expected a JSON object'),
        ]
        for index, (bad, detail) in enumerate(variants):
            with self.subTest(detail=detail):
                self.output = self.root / f"field-error-{index}"
                raw = json.dumps(response_fixture([
                    claim_fixture(), {**claim_fixture(), "claim_id": "C02"}, bad])).encode()
                with patch.object(decomposer.generator, "request_review", return_value=(200, None, raw)) as request:
                    self.assertEqual(self.run_decomposition(), "invalid_output")
                request.assert_called_once()
                error = f"claims[2]: {detail}."
                validation = json.loads((self.output / "validation.json").read_bytes())
                self.assertEqual(validation["errors"], [error])
                self.assertEqual(self.manifest()["error"], f"ValueError: {error}")
                self.assertEqual((self.output / "decomposition_raw.json").read_bytes(), raw)
                self.assertFalse((self.output / "claims.jsonl").exists())

    def test_empty_claims_are_recorded_without_retry(self):
        with patch.object(decomposer.generator, "request_review", return_value=(
                200, None, json.dumps(response_fixture([])).encode())) as request:
            self.assertEqual(self.run_decomposition(), "no_claims")
        request.assert_called_once()
        self.assertEqual((self.output / "claims.jsonl").read_bytes(), b"")
        self.assertEqual(self.manifest()["claim_count"], 0)
        self.assertNotIn("reasoning_effort", json.loads((self.output / "request.json").read_bytes()))

    def test_bad_provider_envelopes_and_duplicate_keys(self):
        variants = []
        for reason in ("length", "content_filter", "tool_calls"):
            response = response_fixture([])
            response["choices"][0]["finish_reason"] = reason
            variants.append(json.dumps(response).encode())
        for field, value in (("refusal", "refused"), ("tool_calls", [{}]), ("content", None),
                             ("content", '{"schema_version":"1","claims":[],"claims":[]}')):
            response = response_fixture([])
            response["choices"][0]["message"][field] = value
            variants.append(json.dumps(response).encode())
        variants.extend([b"{", b"[]", b'{"choices":[]}', b'{"choices":[{}]}'])
        for index, raw in enumerate(variants):
            with self.subTest(raw=raw):
                self.output = self.root / f"invalid-{index}"
                with patch.object(decomposer.generator, "request_review", return_value=(200, None, raw)) as request:
                    self.assertEqual(self.run_decomposition(), "invalid_output")
                request.assert_called_once()
                self.assertFalse((self.output / "claims.jsonl").exists())

    def test_transport_and_provider_errors_remain_run_errors(self):
        for index, result in enumerate(((429, None, b"rate limit"),
                                        (200, None, b'{"error":{"code":503}}'))):
            self.output = self.root / f"error-{index}"
            with patch.object(decomposer.generator, "request_review", return_value=result) as request:
                self.assertEqual(self.run_decomposition(), "run_error")
            request.assert_called_once()
            self.assertFalse((self.output / "claims.jsonl").exists())
        self.output = self.root / "network-error"
        with patch.object(decomposer.generator, "request_review", side_effect=URLError("offline")) as request:
            self.assertEqual(self.run_decomposition(), "run_error")
        request.assert_called_once()
        self.assertFalse((self.output / "decomposition_raw.json").exists())

    def test_missing_key_sends_nothing(self):
        with patch.object(decomposer.generator, "load_api_key", return_value=""):
            with patch.object(decomposer.generator, "request_review") as request:
                self.assertEqual(self.run_decomposition(), "run_error")
        request.assert_not_called()
        self.assertEqual(self.manifest()["request_attempts"], 0)
        self.assertTrue((self.output / "request.json").exists())

    def test_existing_output_is_preserved(self):
        self.output.mkdir()
        marker = self.output / "keep.txt"
        marker.write_bytes(b"previous run")
        with patch.object(decomposer.generator, "request_review") as request:
            with self.assertRaises(FileExistsError):
                self.run_decomposition()
        request.assert_not_called()
        self.assertEqual(marker.read_bytes(), b"previous run")
        self.assertEqual(len(list(self.output.iterdir())), 1)

    def test_invalid_selection_input_or_model_creates_no_run(self):
        for model, budget in (("paid/model", 100), ("openrouter/free", 100), ("test-model", 0)):
            with self.subTest(model=model, budget=budget), self.assertRaises(ValueError):
                decomposer.decompose_findings(self.input, self.finding["finding_id"], self.output, model, budget)
        for data in (b"", b"not json", b'{"title":"x"}',
                     self.input.read_bytes() * 2,
                     json.dumps({**self.finding, "finding_id": "not-selected"}).encode()):
            self.input.write_bytes(data)
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.run_decomposition()
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
