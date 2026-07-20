from __future__ import annotations

import hashlib
import json
import sysconfig
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, NamedTuple

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

SCHEMA_FILES_V2: dict[str, str] = {
    "assessment_request": "assessment-request.v2.schema.json",
    "classification": "classification.v2.schema.json",
    "closure_receipt": "closure-receipt.v2.schema.json",
    "evidence_profile": "evidence-profile.v2.schema.json",
    "transition_assessment": "transition-assessment.v2.schema.json",
    "verification_receipt": "verification-receipt.v2.schema.json",
}

SCHEMA_FILES_BY_VERSION: dict[int, Mapping[str, str]] = {
    1: SCHEMA_FILES,
    2: SCHEMA_FILES_V2,
}

class RequestComponent(NamedTuple):
    field: str
    schema_key: str
    schema_version: int
    repeated: bool = False
    optional: bool = False


REQUEST_COMPONENTS_BY_VERSION: dict[int, tuple[RequestComponent, ...]] = {
    1: (
        RequestComponent("observation", "observation", 1),
        RequestComponent("classification", "classification", 1),
        RequestComponent("effects", "effect_receipt", 1, repeated=True),
        RequestComponent("verifications", "verification_receipt", 1, repeated=True),
        RequestComponent("closure", "closure_receipt", 1, optional=True),
    ),
    2: (
        RequestComponent("observation", "observation", 1),
        RequestComponent("classification", "classification", 2),
        RequestComponent("effects", "effect_receipt", 1, repeated=True),
        RequestComponent("verifications", "verification_receipt", 2, repeated=True),
        RequestComponent("closure", "closure_receipt", 2, optional=True),
    ),
}

SOURCE_CURRENT = "current"
VERIFICATION_PASS = "pass"
VERIFICATION_FAIL = "fail"
CLOSURE_CLOSED = "closed"
TARGET_CRITICALITY_UNKNOWN = "unknown"
DEGRADED_MODE_BOUNDED = "bounded"
COMMON_MODE_INDEPENDENT = "independent"
SPLIT_BRAIN_NEGATIVE_CONTROL = "split_brain_negative_control"

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
        candidates.append(Path(sysconfig.get_path("data")) / "share" / "konvergenzregelkreis")

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
            raise ContractValidationError([f"json:too_large:{path}:{size}:{MAX_JSON_BYTES}"])
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractValidationError([f"file:not_found:{path}"]) from exc
    except json.JSONDecodeError as exc:
        raise ContractValidationError(
            [f"json:invalid:{path}:{exc.lineno}:{exc.colno}:{exc.msg}"]
        ) from exc


def _all_schema_files() -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                filename
                for schema_files in SCHEMA_FILES_BY_VERSION.values()
                for filename in schema_files.values()
            }
        )
    )


def _schema_registry(root: Path) -> Registry:
    registry = Registry()
    errors: list[str] = []
    for filename in _all_schema_files():
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


def _schema(root: Path, key: str, *, version: int = 1) -> Mapping[str, Any]:
    files = SCHEMA_FILES_BY_VERSION.get(version, {})
    try:
        filename = files[key]
    except KeyError as exc:
        raise ContractValidationError([f"schema:unknown:v{version}:{key}"]) from exc
    schema = load_json(root / "protocol" / filename)
    if not isinstance(schema, dict):
        raise ContractValidationError([f"schema:not_object:{filename}"])
    return schema


def _validate(
    root: Path,
    schema_key: str,
    instance: Any,
    prefix: str,
    *,
    version: int = 1,
) -> None:
    schema = _schema(root, schema_key, version=version)
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


def _read_profile_bytes(path: Path, profile_id: str) -> bytes:
    if not path.exists():
        raise ContractValidationError([f"profile:not_found:{profile_id}"])
    raw = path.read_bytes()
    if not raw:
        raise ContractValidationError([f"profile:empty:{profile_id}"])
    return raw


def load_profile(root: Path, risk_level: str) -> tuple[Mapping[str, Any], str]:
    path = _profile_path(root, risk_level)
    raw = _read_profile_bytes(path, risk_level)
    profile = load_json(path)
    _validate(root, "evidence_profile", profile, f"profile:{risk_level}")
    if profile["risk_level"] != risk_level:
        raise ContractValidationError([f"profile:risk_level_mismatch:{risk_level}"])
    return profile, hashlib.sha256(raw).hexdigest()


def _resilience_profile_index(
    profile: Mapping[str, Any],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    cells = list(profile.get("cells", []))
    keys = [
        (str(item.get("change_risk")), str(item.get("target_criticality")))
        for item in cells
    ]
    counts = Counter(keys)
    duplicates = sorted(key for key, count in counts.items() if count > 1)
    if duplicates:
        rendered = ",".join(
            f"{risk}-{criticality}:count={counts[(risk, criticality)]}"
            for risk, criticality in duplicates
        )
        raise ContractValidationError(
            [f"profile:resilience.v2:duplicate_cell:{rendered}"]
        )

    criticalities = {"optional", "supporting", "essential", "foundational", "unknown"}
    expected = {
        (f"R{risk}", criticality)
        for risk in range(4)
        for criticality in criticalities
    }
    actual = set(keys)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ContractValidationError(
            [
                f"profile:resilience.v2:matrix_incomplete:missing={missing}:extra={extra}"
            ]
        )
    return {key: cell for key, cell in zip(keys, cells, strict=True)}


def _load_resilience_profile_bundle(
    root: Path,
) -> tuple[Mapping[str, Any], str, dict[tuple[str, str], Mapping[str, Any]]]:
    path = root / "profiles" / "resilience.v2.json"
    raw = _read_profile_bytes(path, "resilience.v2")
    profile = load_json(path)
    _validate(root, "evidence_profile", profile, "profile:resilience.v2", version=2)
    index = _resilience_profile_index(profile)
    return profile, hashlib.sha256(raw).hexdigest(), index


def load_resilience_profile(root: Path) -> tuple[Mapping[str, Any], str]:
    profile, profile_sha256, _ = _load_resilience_profile_bundle(root)
    return profile, profile_sha256


def _resilience_profile_cell(
    profile_index: Mapping[tuple[str, str], Mapping[str, Any]],
    change_risk: str,
    target_criticality: str,
) -> Mapping[str, Any]:
    try:
        return profile_index[(change_risk, target_criticality)]
    except KeyError as exc:
        raise ContractValidationError(
            [f"profile:resilience.v2:cell_not_found:{change_risk}:{target_criticality}"]
        ) from exc


def _validate_request_version(
    root: Path, request: Mapping[str, Any], version: int
) -> None:
    _validate(root, "assessment_request", request, "request", version=version)
    for component in REQUEST_COMPONENTS_BY_VERSION[version]:
        if component.optional and component.field not in request:
            continue
        value = request[component.field]
        if component.repeated:
            for index, item in enumerate(value):
                _validate(
                    root,
                    component.schema_key,
                    item,
                    f"{component.field}[{index}]",
                    version=component.schema_version,
                )
        else:
            _validate(
                root,
                component.schema_key,
                value,
                component.field,
                version=component.schema_version,
            )


def validate_request(root: Path, request: Any) -> Mapping[str, Any]:
    if not isinstance(request, dict):
        raise ContractValidationError(["request:not_object"])
    version = request.get("schema_version")
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version not in REQUEST_COMPONENTS_BY_VERSION
    ):
        raise ContractValidationError([f"request:schema_version:unsupported:{version}"])
    _validate_request_version(root, request, version)
    return request


def validate_contracts(root: Path) -> dict[str, Any]:
    schema_names: list[str] = []
    for filename in _all_schema_files():
        schema = load_json(root / "protocol" / filename)
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            raise ContractValidationError([f"schema:invalid:{filename}:{exc}"]) from exc
        schema_names.append(filename)

    profile_names: list[str] = []
    for risk_level in ("R0", "R1", "R2", "R3"):
        load_profile(root, risk_level)
        profile_names.append(f"{risk_level}.v1.json")
    load_resilience_profile(root)
    profile_names.append("resilience.v2.json")

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
    return {str(item["kind"]) for item in receipts if item["result"] == VERIFICATION_PASS}


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


def _evidence_state(
    effects: list[Mapping[str, Any]],
    verifications: list[Mapping[str, Any]],
    required_effects: Iterable[str],
    required_verifications: Iterable[str],
    closure: Mapping[str, Any] | None,
    required_closure_fields: list[str],
) -> tuple[list[str], list[str], list[str]]:
    conflicts = sorted(
        set(_conflicts(effects, "effect") + _conflicts(verifications, "verification"))
    )
    failed_verifications = sorted(
        {
            f"verification:{receipt['kind']}:fail"
            for receipt in verifications
            if receipt["result"] == VERIFICATION_FAIL
        }
    )
    present_effects = {str(item["kind"]) for item in effects}
    present_verifications = _present_pass_verifications(verifications)
    missing = [
        f"effect:{kind}" for kind in required_effects if kind not in present_effects
    ]
    missing.extend(
        f"verification:{kind}"
        for kind in required_verifications
        if kind not in present_verifications
    )
    missing.extend(_missing_closure_fields(closure, required_closure_fields))
    return conflicts, failed_verifications, sorted(set(missing))


def _resolve_status(
    *,
    conflicts: list[str],
    source_states: Mapping[str, str],
    blocked_by: list[str],
    missing: list[str],
    closure: Mapping[str, Any] | None,
) -> tuple[str, list[str]]:
    blocked = sorted(set(blocked_by))
    if conflicts:
        return "conflicting_evidence", blocked

    stale_sources = sorted(
        f"{name}:{state}"
        for name, state in source_states.items()
        if state != SOURCE_CURRENT
    )
    if stale_sources:
        return "source_stale", sorted(set(blocked + stale_sources))
    if blocked:
        return "blocked", blocked
    if missing:
        return "evidence_missing", blocked
    if closure is not None and closure["status"] == CLOSURE_CLOSED:
        return "terminally_closed", blocked
    return "transition_allowed", blocked


def _evaluate_v1(validated: Mapping[str, Any], root: Path) -> dict[str, Any]:
    risk_level = str(validated["risk_level"])
    profile, profile_sha256 = load_profile(root, risk_level)
    effects = list(validated["effects"])
    verifications = list(validated["verifications"])
    closure = validated.get("closure")
    conflicts, failed_verifications, missing = _evidence_state(
        effects,
        verifications,
        profile["required_effects"],
        profile["required_verifications"],
        closure,
        list(profile["required_closure_fields"]),
    )
    status, blocked_by = _resolve_status(
        conflicts=conflicts,
        source_states={"source_state": str(validated["observation"]["source_state"])},
        blocked_by=list(validated["classification"]["blocked_by"]) + failed_verifications,
        missing=missing,
        closure=closure,
    )

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


def _resilience_conflicts(classification: Mapping[str, Any]) -> list[str]:
    resilience = classification["resilience"]
    primary = str(resilience["primary_failure_domain"])
    recovery = resilience["recovery_failure_domain"]
    common_mode = str(resilience["common_mode_risk"])
    domains = set(classification["affected_failure_domains"])
    conflicts: list[str] = []
    if primary not in domains:
        conflicts.append("classification:primary_failure_domain:not_affected")
    if recovery is not None and recovery not in domains:
        conflicts.append("classification:recovery_failure_domain:not_affected")
    if common_mode == "independent" and recovery == primary:
        conflicts.append("classification:common_mode_risk:independence_contradiction")
    if common_mode == "same-failure-domain" and recovery is not None and recovery != primary:
        conflicts.append("classification:common_mode_risk:same_domain_contradiction")
    return conflicts


def _evaluate_v2(validated: Mapping[str, Any], root: Path) -> dict[str, Any]:
    classification = validated["classification"]
    change_risk = str(classification["change_risk"])
    target_criticality = str(classification["target_criticality"])
    profile, profile_sha256, profile_index = _load_resilience_profile_bundle(root)
    cell = _resilience_profile_cell(profile_index, change_risk, target_criticality)

    effects = list(validated["effects"])
    verifications = list(validated["verifications"])
    resilience = classification["resilience"]
    required_verifications = list(cell["required_verifications"])
    if cell["requires_resilience_evidence"] and resilience["split_brain_possible"]:
        required_verifications.append(SPLIT_BRAIN_NEGATIVE_CONTROL)

    closure = validated.get("closure")
    conflicts, failed_verifications, missing = _evidence_state(
        effects,
        verifications,
        cell["required_effects"],
        required_verifications,
        closure,
        list(cell["required_closure_fields"]),
    )
    conflicts = sorted(set(conflicts + _resilience_conflicts(classification)))

    blocked_by = list(classification["blocked_by"]) + failed_verifications
    if target_criticality == TARGET_CRITICALITY_UNKNOWN:
        blocked_by.append("target_criticality:unknown")
    if cell["requires_resilience_evidence"]:
        if resilience["recovery_failure_domain"] is None:
            blocked_by.append("resilience:recovery_failure_domain:missing")
        if resilience["degraded_mode"] != DEGRADED_MODE_BOUNDED:
            blocked_by.append(f"resilience:degraded_mode:{resilience['degraded_mode']}")
        if not resilience["return_to_primary_required"]:
            blocked_by.append("resilience:return_to_primary:not_required")
    if (
        cell["requires_independent_recovery"]
        and resilience["common_mode_risk"] != COMMON_MODE_INDEPENDENT
    ):
        blocked_by.append(f"resilience:common_mode_risk:{resilience['common_mode_risk']}")

    status, blocked_by = _resolve_status(
        conflicts=conflicts,
        source_states={
            "source_state": str(validated["observation"]["source_state"]),
            "criticality_source_state": str(classification["criticality_source_state"]),
        },
        blocked_by=blocked_by,
        missing=missing,
        closure=closure,
    )

    result = {
        "schema_version": 2,
        "assessment_id": validated["assessment_id"],
        "change_risk": change_risk,
        "target_criticality": target_criticality,
        "status": status,
        "missing_evidence": missing,
        "conflicts": conflicts,
        "blocked_by": blocked_by,
        "profile_id": profile["profile_id"],
        "profile_cell_id": cell["cell_id"],
        "profile_sha256": profile_sha256,
    }
    _validate(root, "transition_assessment", result, "result", version=2)
    return result


EVALUATORS_BY_VERSION: dict[
    int, Callable[[Mapping[str, Any], Path], dict[str, Any]]
] = {
    1: _evaluate_v1,
    2: _evaluate_v2,
}


def evaluate(request: Any, root: Path) -> dict[str, Any]:
    validated = validate_request(root, request)
    version = int(validated["schema_version"])
    try:
        evaluator = EVALUATORS_BY_VERSION[version]
    except KeyError as exc:
        raise ContractValidationError(
            [f"request:schema_version:unsupported:{version}"]
        ) from exc
    return evaluator(validated, root)
