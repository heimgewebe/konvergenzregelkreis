from __future__ import annotations

import hashlib
import json
import sysconfig
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SCHEMA_FILES: dict[str, str] = {
    "assessment_request": "assessment-request.v1.schema.json",
    "classification": "classification.v1.schema.json",
    "closure_receipt": "closure-receipt.v1.schema.json",
    "effect_receipt": "effect-receipt.v1.schema.json",
    "evidence_profile": "evidence-profile.v1.schema.json",
    "observation": "observation.v1.schema.json",
    "transition_assessment": "transition-assessment.v1.schema.json",
    "verification_receipt": "verification-receipt.v1.schema.json",
}

MAX_JSON_BYTES = 4 * 1024 * 1024

STATUS_EXIT_CODES: dict[str, int] = {
    "transition_allowed": 0,
    "terminally_closed": 0,
    "evidence_missing": 2,
    "conflicting_evidence": 4,
    "source_stale": 5,
    "blocked": 6,
}


class ContractValidationError(ValueError):
    """Raised when an input, profile, schema, or output violates the contract."""

    def __init__(self, errors: Iterable[str]):
        self.errors = tuple(sorted(set(errors)))
        super().__init__("; ".join(self.errors))


def canonical_json(data: Any, *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"


def locate_contract_root(explicit: str | Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(Path(explicit))
    else:
        candidates.extend([Path.cwd(), Path(__file__).resolve().parents[2]])
        candidates.append(
            Path(sysconfig.get_path("data")) / "share" / "konvergenzregelkreis"
        )

    for candidate in candidates:
        root = candidate.resolve()
        if (root / "protocol").is_dir() and (root / "profiles").is_dir():
            return root

    rendered = ", ".join(str(path) for path in candidates)
    raise ContractValidationError([f"contract_root:not_found:{rendered}"])


def load_json(path: Path) -> Any:
    try:
        size = path.stat().st_size
        if size > MAX_JSON_BYTES:
            raise ContractValidationError(
                [f"json:too_large:{path}:{size}:{MAX_JSON_BYTES}"]
            )
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractValidationError([f"file:not_found:{path}"]) from exc
    except json.JSONDecodeError as exc:
        raise ContractValidationError(
            [f"json:invalid:{path}:{exc.lineno}:{exc.colno}:{exc.msg}"]
        ) from exc


def _schema_registry(root: Path) -> Registry:
    registry = Registry()
    errors: list[str] = []
    for filename in sorted(set(SCHEMA_FILES.values())):
        contents = load_json(root / "protocol" / filename)
        if not isinstance(contents, dict):
            errors.append(f"schema:not_object:{filename}")
            continue
        schema_id = contents.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            errors.append(f"schema:missing_id:{filename}")
            continue
        try:
            resource = Resource.from_contents(contents)
        except Exception as exc:
            errors.append(f"schema:resource_invalid:{filename}:{exc}")
            continue
        registry = registry.with_resource(schema_id, resource)
    if errors:
        raise ContractValidationError(errors)
    return registry


def _schema(root: Path, key: str) -> Mapping[str, Any]:
    try:
        filename = SCHEMA_FILES[key]
    except KeyError as exc:
        raise ContractValidationError([f"schema:unknown:{key}"]) from exc
    schema = load_json(root / "protocol" / filename)
    if not isinstance(schema, dict):
        raise ContractValidationError([f"schema:not_object:{filename}"])
    return schema


def _validate(root: Path, schema_key: str, instance: Any, prefix: str) -> None:
    schema = _schema(root, schema_key)
    validator = Draft202012Validator(
        schema,
        registry=_schema_registry(root),
        format_checker=FormatChecker(),
    )
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: item.json_path):
        errors.append(f"{prefix}:{error.json_path}:{error.message}")
    if errors:
        raise ContractValidationError(errors)


def _profile_path(root: Path, risk_level: str) -> Path:
    return root / "profiles" / f"{risk_level}.v1.json"


def load_profile(root: Path, risk_level: str) -> tuple[Mapping[str, Any], str]:
    path = _profile_path(root, risk_level)
    raw = path.read_bytes() if path.exists() else b""
    if not raw:
        raise ContractValidationError([f"profile:not_found:{risk_level}"])
    profile = load_json(path)
    _validate(root, "evidence_profile", profile, f"profile:{risk_level}")
    if profile["risk_level"] != risk_level:
        raise ContractValidationError([f"profile:risk_level_mismatch:{risk_level}"])
    return profile, hashlib.sha256(raw).hexdigest()


def validate_request(root: Path, request: Any) -> Mapping[str, Any]:
    _validate(root, "assessment_request", request, "request")
    if not isinstance(request, dict):
        raise ContractValidationError(["request:not_object"])

    _validate(root, "observation", request["observation"], "observation")
    _validate(root, "classification", request["classification"], "classification")
    for index, receipt in enumerate(request["effects"]):
        _validate(root, "effect_receipt", receipt, f"effects[{index}]")
    for index, receipt in enumerate(request["verifications"]):
        _validate(root, "verification_receipt", receipt, f"verifications[{index}]")
    if "closure" in request:
        _validate(root, "closure_receipt", request["closure"], "closure")
    return request


def validate_contracts(root: Path) -> dict[str, Any]:
    schema_names: list[str] = []
    for key, filename in sorted(SCHEMA_FILES.items()):
        schema = _schema(root, key)
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # jsonschema exposes several schema exception types
            raise ContractValidationError([f"schema:invalid:{filename}:{exc}"]) from exc
        schema_names.append(filename)

    profile_names: list[str] = []
    for risk_level in ("R0", "R1", "R2", "R3"):
        load_profile(root, risk_level)
        profile_names.append(f"{risk_level}.v1.json")

    return {
        "schema_version": 1,
        "status": "valid",
        "profiles": profile_names,
        "schemas": schema_names,
    }


def _conflicts(receipts: list[Mapping[str, Any]], category: str) -> list[str]:
    by_kind: dict[str, set[str]] = {}
    for receipt in receipts:
        by_kind.setdefault(str(receipt["kind"]), set()).add(str(receipt["subject_sha256"]))
    return [
        f"{category}:{kind}:subject_sha256"
        for kind, values in sorted(by_kind.items())
        if len(values) > 1
    ]


def _present_pass_verifications(receipts: list[Mapping[str, Any]]) -> set[str]:
    return {str(item["kind"]) for item in receipts if item["result"] == "pass"}


def _missing_closure_fields(
    closure: Mapping[str, Any] | None, required_fields: list[str]
) -> list[str]:
    if not required_fields:
        return []
    if closure is None:
        return ["closure"] + [f"closure.{field}" for field in required_fields]

    missing: list[str] = []
    for field in required_fields:
        value = closure.get(field)
        if value is None or value == "" or value == []:
            missing.append(f"closure.{field}")
    return missing


def evaluate(request: Any, root: Path) -> dict[str, Any]:
    validated = validate_request(root, request)
    risk_level = str(validated["risk_level"])
    profile, profile_sha256 = load_profile(root, risk_level)

    effects = list(validated["effects"])
    verifications = list(validated["verifications"])
    conflicts = sorted(
        set(_conflicts(effects, "effect") + _conflicts(verifications, "verification"))
    )

    blocked_by = list(validated["classification"]["blocked_by"])
    for receipt in verifications:
        if receipt["result"] == "fail":
            blocked_by.append(f"verification:{receipt['kind']}:fail")
    blocked_by = sorted(set(blocked_by))

    present_effects = {str(item["kind"]) for item in effects}
    present_verifications = _present_pass_verifications(verifications)
    missing = [
        f"effect:{kind}"
        for kind in profile["required_effects"]
        if kind not in present_effects
    ]
    missing.extend(
        f"verification:{kind}"
        for kind in profile["required_verifications"]
        if kind not in present_verifications
    )

    closure = validated.get("closure")
    missing.extend(
        _missing_closure_fields(closure, list(profile["required_closure_fields"]))
    )
    missing = sorted(set(missing))

    source_state = validated["observation"]["source_state"]
    if conflicts:
        status = "conflicting_evidence"
    elif source_state != "current":
        status = "source_stale"
        blocked_by = sorted(set(blocked_by + [f"source_state:{source_state}"]))
    elif blocked_by:
        status = "blocked"
    elif missing:
        status = "evidence_missing"
    elif closure is not None and closure["status"] == "closed":
        status = "terminally_closed"
    else:
        status = "transition_allowed"

    result = {
        "schema_version": 1,
        "assessment_id": validated["assessment_id"],
        "risk_level": risk_level,
        "status": status,
        "missing_evidence": missing,
        "conflicts": conflicts,
        "blocked_by": blocked_by,
        "profile_sha256": profile_sha256,
    }
    _validate(root, "transition_assessment", result, "result")
    return result
