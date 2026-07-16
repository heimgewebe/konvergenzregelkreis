from __future__ import annotations

import copy
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import regelkreis
from regelkreis.cli import main
from regelkreis.core import (
    MAX_JSON_BYTES,
    ContractValidationError,
    canonical_json,
    evaluate,
    load_json,
    validate_contracts,
)

ROOT = Path(__file__).resolve().parents[1]
VALID_FIXTURE = ROOT / "conformance" / "valid" / "r2-terminal.json"
EXPECTED_FIXTURE = ROOT / "conformance" / "expected" / "r2-terminal.json"
PILOT_FIXTURE = ROOT / "conformance" / "valid" / "systemkatalog-pilot-r2-terminal.json"
PILOT_EXPECTED = ROOT / "conformance" / "expected" / "systemkatalog-pilot-r2-terminal.json"
GRABOWSKI_PILOT = ROOT / "conformance" / "valid" / "grabowski-pilot-r2-terminal.json"
GRABOWSKI_EXPECTED = ROOT / "conformance" / "expected" / "grabowski-pilot-r2-terminal.json"
GRABOWSKI_CONFLICT = ROOT / "conformance" / "conflict" / "grabowski-pilot-r2-conflicting-deployment.json"
GRABOWSKI_CONFLICT_EXPECTED = ROOT / "conformance" / "expected" / "grabowski-pilot-r2-conflicting-deployment.json"
INVALID_FIXTURE = ROOT / "conformance" / "invalid" / "missing-source-refs.json"


class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = load_json(VALID_FIXTURE)

    def test_all_contracts_are_valid(self) -> None:
        result = validate_contracts(ROOT)
        self.assertEqual("valid", result["status"])
        self.assertEqual(4, len(result["profiles"]))
        self.assertEqual(8, len(result["schemas"]))

    def test_r2_terminal_fixture_matches_expected(self) -> None:
        self.assertEqual(load_json(EXPECTED_FIXTURE), evaluate(self.request, ROOT))

    def test_systemkatalog_pilot_fixture_matches_expected(self) -> None:
        self.assertEqual(load_json(PILOT_EXPECTED), evaluate(load_json(PILOT_FIXTURE), ROOT))

    def test_grabowski_pilot_fixture_matches_expected(self) -> None:
        self.assertEqual(load_json(GRABOWSKI_EXPECTED), evaluate(load_json(GRABOWSKI_PILOT), ROOT))

    def test_grabowski_conflict_fixture_fails_closed(self) -> None:
        self.assertEqual(
            load_json(GRABOWSKI_CONFLICT_EXPECTED),
            evaluate(load_json(GRABOWSKI_CONFLICT), ROOT),
        )

    def test_package_and_module_versions_match(self) -> None:
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version = "([^"]+)"$', text, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), regelkreis.__version__)

    def test_output_is_byte_deterministic(self) -> None:
        first = canonical_json(evaluate(self.request, ROOT))
        second = canonical_json(evaluate(copy.deepcopy(self.request), ROOT))
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))

    def test_missing_evidence_is_named_exactly(self) -> None:
        request = copy.deepcopy(self.request)
        request["verifications"] = [
            item for item in request["verifications"] if item["kind"] != "negative_control"
        ]
        request["closure"]["cleanup_evidence"] = []
        result = evaluate(request, ROOT)
        self.assertEqual("evidence_missing", result["status"])
        self.assertEqual(
            ["closure.cleanup_evidence", "verification:negative_control"],
            result["missing_evidence"],
        )

    def test_conflicting_subject_hashes_fail_closed(self) -> None:
        request = copy.deepcopy(self.request)
        conflicting = copy.deepcopy(request["effects"][0])
        conflicting["subject_sha256"] = "9999999999999999999999999999999999999999999999999999999999999999"
        request["effects"].append(conflicting)
        result = evaluate(request, ROOT)
        self.assertEqual("conflicting_evidence", result["status"])
        self.assertEqual(["effect:merge:subject_sha256"], result["conflicts"])

    def test_stale_source_has_precedence_over_missing_evidence(self) -> None:
        request = copy.deepcopy(self.request)
        request["observation"]["source_state"] = "stale"
        request["verifications"] = []
        result = evaluate(request, ROOT)
        self.assertEqual("source_stale", result["status"])
        self.assertEqual(["source_state:stale"], result["blocked_by"])
        self.assertIn("verification:tests", result["missing_evidence"])

    def test_explicit_blocker_fails_closed(self) -> None:
        request = copy.deepcopy(self.request)
        request["classification"]["blocked_by"] = ["foreign_active_lease"]
        result = evaluate(request, ROOT)
        self.assertEqual("blocked", result["status"])
        self.assertEqual(["foreign_active_lease"], result["blocked_by"])

    def test_failed_verification_blocks(self) -> None:
        request = copy.deepcopy(self.request)
        request["verifications"][0]["result"] = "fail"
        result = evaluate(request, ROOT)
        self.assertEqual("blocked", result["status"])
        self.assertIn("verification:tests:fail", result["blocked_by"])
        self.assertIn("verification:tests", result["missing_evidence"])

    def test_invalid_fixture_is_rejected(self) -> None:
        with self.assertRaises(ContractValidationError) as raised:
            evaluate(load_json(INVALID_FIXTURE), ROOT)
        self.assertTrue(any("source_refs" in item for item in raised.exception.errors))

    def test_oversized_json_is_rejected_before_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.json"
            path.write_bytes(b" " * (MAX_JSON_BYTES + 1))
            with self.assertRaises(ContractValidationError) as raised:
                load_json(path)
        self.assertTrue(any("json:too_large" in item for item in raised.exception.errors))

    def test_cli_exit_codes_and_streams(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["evaluate", str(VALID_FIXTURE), "--contract-root", str(ROOT)])
        self.assertEqual(0, code)
        self.assertEqual("", stderr.getvalue())
        self.assertEqual("terminally_closed", json.loads(stdout.getvalue())["status"])

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["evaluate", str(INVALID_FIXTURE), "--contract-root", str(ROOT)])
        self.assertEqual(3, code)
        self.assertEqual("", stdout.getvalue())
        self.assertEqual("invalid_input", json.loads(stderr.getvalue())["status"])

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["evaluate", str(GRABOWSKI_CONFLICT), "--contract-root", str(ROOT)])
        self.assertEqual(4, code)
        self.assertEqual("", stderr.getvalue())
        self.assertEqual("conflicting_evidence", json.loads(stdout.getvalue())["status"])


if __name__ == "__main__":
    unittest.main()
