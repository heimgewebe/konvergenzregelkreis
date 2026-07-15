from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .core import (
    STATUS_EXIT_CODES,
    ContractValidationError,
    canonical_json,
    evaluate,
    load_json,
    locate_contract_root,
    validate_contracts,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="regelkreis",
        description="Zustandslose Auswertung beleggebundener Konvergenzübergänge.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Bewerte eine Assessment-Request-Datei."
    )
    evaluate_parser.add_argument("request", type=Path)
    evaluate_parser.add_argument("--contract-root", type=Path)
    evaluate_parser.add_argument("--pretty", action="store_true")

    validate_parser = subparsers.add_parser(
        "validate-contracts", help="Prüfe alle Schemas und Evidence-Profile."
    )
    validate_parser.add_argument("--contract-root", type=Path)
    validate_parser.add_argument("--pretty", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        root = locate_contract_root(args.contract_root)
        if args.command == "validate-contracts":
            result = validate_contracts(root)
            sys.stdout.write(canonical_json(result, pretty=args.pretty))
            return 0

        request = load_json(args.request.resolve())
        result = evaluate(request, root)
        sys.stdout.write(canonical_json(result, pretty=args.pretty))
        return STATUS_EXIT_CODES[result["status"]]
    except ContractValidationError as exc:
        error = {
            "schema_version": 1,
            "status": "invalid_input",
            "errors": list(exc.errors),
        }
        sys.stderr.write(canonical_json(error))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
