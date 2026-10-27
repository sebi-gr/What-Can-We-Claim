"""Offline checks with synthetic claims and a mocked provider; no live API calls."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("claim_experiment", PROJECT / "run.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def sample_claim(file="Sample.java", line=1, quote="return value;"):
    return {"id": "C01", "proposition": "Der sichtbare Code gibt value zurück.",
            "family": "data_flow", "subtype": None, "family_reason": "Rückgabe eines Werts.",
            "qualifiers": ["Synthetischer Test, kein Forschungsresultat."],
            "evidence": [{"file": file, "line_start": line, "line_end": line, "quote": quote}],
            "context_claim_ids": []}


def provider_response(text, status="completed"):
    return {"id": "synthetic-response", "status": status,
            "usage": {"input_tokens": 100, "output_tokens": 25},
            "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="wcwv-offline-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.output = self.root / "result"
        self.schema = json.loads((PROJECT / "resources/claim_schema.json").read_text())
        self.prompts = json.loads((PROJECT / "resources/prompts.json").read_text())
        resources = self.root / "resources"
        resources.mkdir()
        for name, value in [("claim_schema.json", self.schema), ("prompts.json", self.prompts)]:
            (resources / name).write_text(json.dumps(value))
        entries = []
        for case in runner.CASES:
            directory = self.root / "examples" / case
            (directory / "code").mkdir(parents=True)
            text = "return value; // SOURCE_ONLY_" + case + "\n"
            source = directory / "code/Sample.java"
            source.write_text(text)
            start = 84 if case == "jackson-xml" else 1
            entries.append({"role": "allowed_code", "path": case + "/code/Sample.java",
                            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                            "original_lines": [start, start]})
            (directory / "baseline.json").write_text(json.dumps({"claims": [sample_claim(line=start)]}))
            (directory / "report.jsonl").write_text("OLD_REPORT_ONLY")
            (directory / "code/not-selected.java").write_text("UNSELECTED_CODE_ONLY")
        (self.root / "examples/sources.json").write_text(json.dumps({"files": entries}))
        (self.root / ".env").write_text("OPENAI_API_KEY='FILE_FAKE_SECRET'\nOTHER=OTHER_SECRET\n")
        self.original_context_builder = runner.build_code_context

    def invoke(self, api, budget=2, output=None, dry_run=False):
        arguments = ["--output", str(output or self.output), "--budget-usd", str(budget)]
        if dry_run:
            arguments.append("--dry-run")
        with patch.object(runner, "ROOT", self.root), \
                patch.object(runner, "build_code_context",
                             side_effect=lambda case: self.original_context_builder(case, self.root)), \
                patch.object(runner, "load_api_key", return_value="PROCESS_FAKE_SECRET"), \
                patch.object(runner, "call_api", api), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return runner.main(arguments)

    def answer_request(self, body, key):
        if "text" not in body:
            return provider_response("REPORT_ONLY Synthetic report.")
        file = body["input"].splitlines()[0].removeprefix("FILE ")
        number, quote = body["input"].splitlines()[1].split(" | ", 1)
        return provider_response(json.dumps({"claims": [sample_claim(file, int(number), quote)]}))

    def test_code_context_excludes_unselected_material(self):
        baseline = self.root / "examples/jspwiki/baseline.json"
        baseline.write_text("BASELINE_ONLY expected answer")
        context, sources, hashes = runner.build_code_context("jspwiki", self.root)
        self.assertIn("SOURCE_ONLY_jspwiki", context)
        self.assertEqual(set(sources), {"Sample.java"})
        self.assertEqual(set(hashes), {"jspwiki/code/Sample.java"})
        for forbidden in ["BASELINE_ONLY", "OLD_REPORT_ONLY", "UNSELECTED_CODE_ONLY",
                          "FILE_FAKE_SECRET", "OTHER_SECRET"]:
            self.assertNotIn(forbidden, context)

    def test_jackson_preserves_original_excerpt_numbers(self):
        context, sources, _ = runner.build_code_context("jackson-xml")
        self.assertEqual(sources["XmlFactory.java.txt"]["line_start"], 84)
        self.assertIn("84 |     public XmlFactory()", context)
        self.assertIn("\n144 |     }", context)
        self.assertNotRegex(context, r"(?m)^1 \|")

    def test_changed_hash_and_symlink_are_rejected(self):
        source = self.root / "examples/jspwiki/code/Sample.java"
        original = source.read_bytes()
        source.write_bytes(original + b"changed")
        with self.assertRaises(ValueError):
            runner.build_code_context("jspwiki", self.root)
        source.unlink()
        outside = self.root / "outside.java"
        outside.write_bytes(original)
        source.symlink_to(outside)
        with self.assertRaises(ValueError):
            runner.build_code_context("jspwiki", self.root)

    def test_valid_and_empty_claims_are_accepted(self):
        sources = {"Sample.java": {"line_start": 1, "text": "return value;\n"}}
        self.assertTrue(runner.validate_claims({"claims": [sample_claim()]}, sources)["valid"])
        result = runner.validate_claims({"claims": []}, sources)
        self.assertTrue(result["valid"])
        self.assertEqual(result["claim_count"], 0)

    def test_invalid_shape_quotes_lines_and_context_are_rejected(self):
        valid = {"claims": [sample_claim()]}
        sources = {"Sample.java": {"line_start": 1, "text": "return value;\n"}}
        mutations = [
            lambda value: value.update(human_reviewed=True),
            lambda value: value["claims"][0].update(truth="proved"),
            lambda value: value["claims"][0]["evidence"][0].update(quote="invented"),
            lambda value: value["claims"][0]["evidence"][0].update(file=".env"),
            lambda value: value["claims"][0]["evidence"][0].update(line_end=2),
            lambda value: value["claims"][0]["evidence"][0].update(line_start=True),
            lambda value: value["claims"][0].update(context_claim_ids=["C01"]),
            lambda value: value["claims"][0].update(context_claim_ids=["missing"]),
            lambda value: value["claims"].append(deepcopy(value["claims"][0])),
            lambda value: value["claims"][0].update(family="exploitability_impact", subtype=None),
            lambda value: value["claims"][0].update(proposition=" "),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                value = deepcopy(valid)
                mutate(value)
                with self.assertRaises(ValueError):
                    runner.validate_claims(value, sources, self.schema)

    def test_request_contract_and_report_only_extraction(self):
        context, _, _ = runner.build_code_context("jspwiki", self.root)
        direct = runner.build_request("code_claims", context, self.prompts, self.schema)
        report = runner.build_request("code_report", context, self.prompts, self.schema)
        text, sources = runner.report_context("REPORT_ONLY Synthetic report.")
        extracted = runner.build_request("report_claims", text, self.prompts, self.schema)
        self.assertEqual(direct["input"], report["input"])
        self.assertEqual(set(sources), {"report.txt"})
        self.assertIn("REPORT_ONLY", extracted["input"])
        self.assertNotIn("SOURCE_ONLY", extracted["input"])
        for body in [direct, report, extracted]:
            self.assertIs(body["store"], False)
            self.assertEqual(body["reasoning"], {"effort": "none"})
            self.assertEqual(body["service_tier"], "default")
            for field in ["tools", "previous_response_id", "Authorization"]:
                self.assertNotIn(field, body)
        self.assertIs(direct["text"]["format"]["strict"], True)
        self.assertEqual(direct["text"]["format"]["type"], "json_schema")

    def test_key_loading_prefers_process_and_reads_only_fake_env(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": " PROCESS_FAKE_SECRET "}, clear=True):
            self.assertEqual(runner.load_api_key(self.root), "PROCESS_FAKE_SECRET")
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(runner.load_api_key(self.root), "FILE_FAKE_SECRET")
            (self.root / ".env").write_text("OTHER=OTHER_SECRET\n")
            with self.assertRaises(ValueError):
                runner.load_api_key(self.root)

    def test_insufficient_budget_blocks_all_requests(self):
        api = Mock(side_effect=self.answer_request)
        with self.assertRaises(ValueError):
            self.invoke(api, budget=0.000001)
        api.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_existing_output_is_never_overwritten(self):
        self.output.mkdir()
        marker = self.output / "keep.txt"
        marker.write_text("keep original")
        api = Mock(side_effect=self.answer_request)
        with self.assertRaises(ValueError):
            self.invoke(api)
        api.assert_not_called()
        self.assertEqual(marker.read_text(), "keep original")

    def test_full_mocked_run_preserves_inputs_without_secrets(self):
        api = Mock(side_effect=self.answer_request)
        originals = {case: (self.root / "examples" / case / "baseline.json").read_bytes()
                     for case in runner.CASES}
        self.assertEqual(self.invoke(api), 0)
        self.assertEqual(api.call_count, 9)
        for case in runner.CASES:
            self.assertEqual((self.output / case / "baseline.json").read_bytes(), originals[case])
            self.assertTrue((self.output / case / "direct.json").is_file())
            self.assertTrue((self.output / case / "prose.json").is_file())
            envelope = json.loads((self.output / case / "report_claims.json").read_text())
            self.assertIn("FILE report.txt", envelope["request"]["input"])
            self.assertNotIn("SOURCE_ONLY", envelope["request"]["input"])
        for path in self.output.rglob("*"):
            if path.is_file():
                for secret in ["PROCESS_FAKE_SECRET", "FILE_FAKE_SECRET", "OTHER_SECRET"]:
                    self.assertNotIn(secret, path.read_text())

    def test_invalid_direct_and_report_preserve_raw_without_retry(self):
        first_direct, first_report = True, True

        def answer(body, key):
            nonlocal first_direct, first_report
            if "text" in body and first_direct:
                first_direct = False
                return provider_response("{invalid JSON")
            if "text" not in body and first_report:
                first_report = False
                return provider_response("unfinished report", status="incomplete")
            return self.answer_request(body, key)

        api = Mock(side_effect=answer)
        self.assertNotEqual(self.invoke(api), 0)
        self.assertEqual(api.call_count, 8)
        first = self.output / runner.CASES[0]
        raw = json.loads((first / "code_claims.json").read_text())
        self.assertEqual(raw["response"]["output"][0]["content"][0]["text"], "{invalid JSON")
        blocked = json.loads((first / "report_claims.json").read_text())
        self.assertIsNone(blocked["request"])
        self.assertFalse((first / "direct.json").exists())
        for case in runner.CASES[1:]:
            self.assertTrue((self.output / case / "direct.json").is_file())
            self.assertTrue((self.output / case / "prose.json").is_file())

    def test_transport_failure_stops_retains_reservation_and_redacts_key(self):
        api = Mock(side_effect=ValueError("synthetic failure PROCESS_FAKE_SECRET"))
        self.assertNotEqual(self.invoke(api), 0)
        api.assert_called_once()
        run = json.loads((self.output / "run.json").read_text())
        self.assertTrue(run["unknown_spend"])
        self.assertGreater(run["reserved_usd"], 0)
        first = json.loads((self.output / runner.CASES[0] / "code_claims.json").read_text())
        self.assertIsNone(first["response"])
        self.assertIn("[REDACTED]", first["error"])
        self.assertNotIn("PROCESS_FAKE_SECRET", json.dumps(first))
        with patch.object(runner.urllib.request, "urlopen", side_effect=urllib.error.URLError("offline")) as url:
            with self.assertRaises(urllib.error.URLError):
                runner.call_api({"input": "synthetic"}, "FAKE_TRANSPORT_KEY")
            url.assert_called_once()


if __name__ == "__main__":
    unittest.main()
