from __future__ import annotations

import copy
import io
import json
import re
import shutil
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
    load_resilience_profile,
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
RESILIENCE_FIXTURE = ROOT / "conformance" / "valid" / "resilience-r2-foundational-terminal.v2.json"
RESILIENCE_EXPECTED = ROOT / "conformance" / "expected" / "resilience-r2-foundational-terminal.v2.json"
RESILIENCE_PROFILE = ROOT / "profiles" / "resilience.v2.json"


class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = load_json(VALID_FIXTURE)

    def test_all_contracts_are_valid(self) -> None:
        result = validate_contracts(ROOT)
        self.assertEqual("valid", result["status"])
        self.assertEqual(5, len(result["profiles"]))
        self.assertEqual(14, len(result["schemas"]))

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


    def test_resilience_v2_fixture_matches_expected(self) -> None:
        self.assertEqual(
            load_json(RESILIENCE_EXPECTED),
            evaluate(load_json(RESILIENCE_FIXTURE), ROOT),
        )

    def test_resilience_v2_output_is_byte_deterministic(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        first = canonical_json(evaluate(request, ROOT))
        second = canonical_json(evaluate(copy.deepcopy(request), ROOT))
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))

    def test_resilience_v2_axes_are_independent(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["classification"]["change_risk"] = "R1"
        request["classification"]["resilience"] = {
            "primary_failure_domain": "host:cluster-a",
            "recovery_failure_domain": None,
            "degraded_mode": "not_applicable",
            "common_mode_risk": "unknown",
            "return_to_primary_required": False,
            "split_brain_possible": False,
        }
        resilience_kinds = {
            "recovery",
            "bounded_degradation",
            "cleanup",
            "return_to_primary",
            "common_mode",
            "split_brain_negative_control",
        }
        request["verifications"] = [
            item for item in request["verifications"] if item["kind"] not in resilience_kinds
        ]
        for field in (
            "recovery_evidence",
            "degraded_mode_evidence",
            "return_to_primary_evidence",
        ):
            request["closure"].pop(field)

        result = evaluate(request, ROOT)
        self.assertEqual("terminally_closed", result["status"])
        self.assertEqual("R1-foundational", result["profile_cell_id"])
        self.assertNotIn("verification:recovery", result["missing_evidence"])

    def test_resilience_v2_missing_recovery_domain_blocks(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["classification"]["resilience"]["recovery_failure_domain"] = None
        result = evaluate(request, ROOT)
        self.assertEqual("blocked", result["status"])
        self.assertIn("resilience:recovery_failure_domain:missing", result["blocked_by"])

    def test_resilience_v2_stale_criticality_fails_closed(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["classification"]["criticality_source_state"] = "stale"
        result = evaluate(request, ROOT)
        self.assertEqual("source_stale", result["status"])
        self.assertIn("criticality_source_state:stale", result["blocked_by"])

    def test_resilience_v2_common_mode_contradiction_is_conflicting(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["classification"]["resilience"]["recovery_failure_domain"] = "host:cluster-a"
        result = evaluate(request, ROOT)
        self.assertEqual("conflicting_evidence", result["status"])
        self.assertIn(
            "classification:common_mode_risk:independence_contradiction",
            result["conflicts"],
        )

    def test_resilience_v2_split_brain_negative_control_is_required(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["verifications"] = [
            item
            for item in request["verifications"]
            if item["kind"] != "split_brain_negative_control"
        ]
        result = evaluate(request, ROOT)
        self.assertEqual("evidence_missing", result["status"])
        self.assertEqual(
            ["verification:split_brain_negative_control"],
            result["missing_evidence"],
        )

    def test_resilience_v2_closure_evidence_is_required(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["closure"]["recovery_evidence"] = []
        request["closure"]["degraded_mode_evidence"] = []
        request["closure"]["return_to_primary_evidence"] = []
        result = evaluate(request, ROOT)
        self.assertEqual("evidence_missing", result["status"])
        self.assertEqual(
            [
                "closure.degraded_mode_evidence",
                "closure.recovery_evidence",
                "closure.return_to_primary_evidence",
            ],
            result["missing_evidence"],
        )

    def test_resilience_v2_profile_is_complete_and_unique(self) -> None:
        profile = load_json(RESILIENCE_PROFILE)
        cells = [
            (item["change_risk"], item["target_criticality"])
            for item in profile["cells"]
        ]
        self.assertEqual(20, len(cells))
        self.assertEqual(20, len(set(cells)))
        self.assertEqual(
            {
                (f"R{risk}", criticality)
                for risk in range(4)
                for criticality in (
                    "optional", "supporting", "essential", "foundational", "unknown"
                )
            },
            set(cells),
        )

    def test_resilience_v2_unknown_target_criticality_blocks(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["classification"]["target_criticality"] = "unknown"
        result = evaluate(request, ROOT)
        self.assertEqual("blocked", result["status"])
        self.assertIn("target_criticality:unknown", result["blocked_by"])
        self.assertEqual("R2-unknown", result["profile_cell_id"])


    def test_missing_resilience_profile_is_reported_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "protocol", root / "protocol")
            (root / "profiles").mkdir()
            with self.assertRaises(ContractValidationError) as raised:
                load_resilience_profile(root)
        self.assertEqual(("profile:not_found:resilience.v2",), raised.exception.errors)

    def test_empty_resilience_profile_is_reported_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "protocol", root / "protocol")
            (root / "profiles").mkdir()
            (root / "profiles" / "resilience.v2.json").write_bytes(b"")
            with self.assertRaises(ContractValidationError) as raised:
                load_resilience_profile(root)
        self.assertEqual(("profile:empty:resilience.v2",), raised.exception.errors)

    def test_resilience_profile_duplicate_names_exact_cell(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "protocol", root / "protocol")
            shutil.copytree(ROOT / "profiles", root / "profiles")
            profile_path = root / "profiles" / "resilience.v2.json"
            profile = load_json(profile_path)
            profile["cells"][-1] = copy.deepcopy(profile["cells"][0])
            profile_path.write_text(json.dumps(profile), encoding="utf-8")
            with self.assertRaises(ContractValidationError) as raised:
                load_resilience_profile(root)
        self.assertIn(
            "profile:resilience.v2:duplicate_cell:R0-optional:count=2",
            raised.exception.errors,
        )

    def test_resilience_v2_split_brain_control_is_conditional(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["classification"]["resilience"]["split_brain_possible"] = False
        request["verifications"] = [
            item
            for item in request["verifications"]
            if item["kind"] != "split_brain_negative_control"
        ]
        result = evaluate(request, ROOT)
        self.assertEqual("terminally_closed", result["status"])
        self.assertNotIn(
            "verification:split_brain_negative_control", result["missing_evidence"]
        )

    def test_resilience_v2_unbounded_or_unknown_degraded_mode_blocks(self) -> None:
        for degraded_mode in ("unbounded", "unknown"):
            with self.subTest(degraded_mode=degraded_mode):
                request = load_json(RESILIENCE_FIXTURE)
                request["classification"]["resilience"]["degraded_mode"] = degraded_mode
                result = evaluate(request, ROOT)
                self.assertEqual("blocked", result["status"])
                self.assertIn(
                    f"resilience:degraded_mode:{degraded_mode}", result["blocked_by"]
                )

    def test_resilience_v2_partially_shared_foundational_recovery_blocks(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["classification"]["resilience"]["common_mode_risk"] = "partially-shared"
        result = evaluate(request, ROOT)
        self.assertEqual("blocked", result["status"])
        self.assertIn(
            "resilience:common_mode_risk:partially-shared", result["blocked_by"]
        )

    def test_resilience_v2_return_to_primary_must_be_required(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["classification"]["resilience"]["return_to_primary_required"] = False
        result = evaluate(request, ROOT)
        self.assertEqual("blocked", result["status"])
        self.assertIn("resilience:return_to_primary:not_required", result["blocked_by"])

    def test_resilience_v2_conflict_precedes_stale_source(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["classification"]["criticality_source_state"] = "stale"
        request["classification"]["resilience"]["recovery_failure_domain"] = "host:cluster-a"
        result = evaluate(request, ROOT)
        self.assertEqual("conflicting_evidence", result["status"])
        self.assertIn(
            "classification:common_mode_risk:independence_contradiction",
            result["conflicts"],
        )
        self.assertNotIn("criticality_source_state:stale", result["blocked_by"])

    def test_resilience_v2_rejects_too_many_failure_domains(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["classification"]["affected_failure_domains"] = [
            f"host:domain-{index}" for index in range(33)
        ]
        request["classification"]["resilience"]["primary_failure_domain"] = "host:domain-0"
        request["classification"]["resilience"]["recovery_failure_domain"] = "host:domain-1"
        with self.assertRaises(ContractValidationError) as raised:
            evaluate(request, ROOT)
        self.assertTrue(
            any("affected_failure_domains" in error for error in raised.exception.errors)
        )

    def test_resilience_v2_rejects_too_many_verifications(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        template = copy.deepcopy(request["verifications"][0])
        request["verifications"] = [copy.deepcopy(template) for _ in range(129)]
        with self.assertRaises(ContractValidationError) as raised:
            evaluate(request, ROOT)
        self.assertTrue(any("verifications" in error for error in raised.exception.errors))

    def test_integral_float_schema_versions_remain_backward_compatible(self) -> None:
        v1_request = load_json(VALID_FIXTURE)
        v1_request["schema_version"] = 1.0
        self.assertEqual("terminally_closed", evaluate(v1_request, ROOT)["status"])

        v2_request = load_json(RESILIENCE_FIXTURE)
        v2_request["schema_version"] = 2.0
        self.assertEqual("terminally_closed", evaluate(v2_request, ROOT)["status"])

    def test_non_scalar_request_schema_version_is_rejected_cleanly(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["schema_version"] = []
        with self.assertRaises(ContractValidationError) as raised:
            evaluate(request, ROOT)
        self.assertIn("request:schema_version:unsupported:[]", raised.exception.errors)

    def test_resilience_v2_invalid_criticality_source_hash_is_rejected(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["classification"]["criticality_source_sha256"] = "not-a-sha256"
        with self.assertRaises(ContractValidationError) as raised:
            evaluate(request, ROOT)
        self.assertTrue(
            any("criticality_source_sha256" in error for error in raised.exception.errors)
        )

    def test_unknown_request_schema_version_is_rejected(self) -> None:
        request = load_json(RESILIENCE_FIXTURE)
        request["schema_version"] = 3
        with self.assertRaises(ContractValidationError) as raised:
            evaluate(request, ROOT)
        self.assertIn("request:schema_version:unsupported:3", raised.exception.errors)


if __name__ == "__main__":
    unittest.main()
