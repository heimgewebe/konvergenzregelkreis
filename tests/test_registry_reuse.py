from __future__ import annotations

import copy
import unittest
from pathlib import Path
from unittest.mock import patch

import regelkreis.core as core

ROOT = Path(__file__).resolve().parents[1]
VALID_FIXTURE = ROOT / "conformance" / "valid" / "r2-terminal.json"


class SchemaRegistryReuseTests(unittest.TestCase):
    def test_validate_request_reuses_registry_only_within_each_call(self) -> None:
        original = core._schema_registry
        calls = 0

        def counted(root: Path):
            nonlocal calls
            calls += 1
            return original(root)

        request = core.load_json(VALID_FIXTURE)
        with patch.object(core, "_schema_registry", side_effect=counted):
            first = core.validate_request(ROOT, request)
            second = core.validate_request(ROOT, copy.deepcopy(request))

        self.assertEqual(request, first)
        self.assertEqual(first, second)
        self.assertEqual(2, calls)


if __name__ == "__main__":
    unittest.main()
