"""The frozen commerce contract, validated with the MCP runtime's jsonschema.

No package installation or producer import happens here. Construction requires
the selected runtime's existing JSON Schema dependency and exact contract bytes.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from mcp_port import CORE_TOOLS, canonical

CONTRACT_SHA256 = "95e864f6dfe44d594a02540c600374127ca5e2152c0c7d60929de2af742eb7bb"


class FrozenCommerceSchemas:
    def __init__(self, path: str | Path):
        raw = Path(path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != CONTRACT_SHA256:
            raise ValueError("Unexpected commerce contract bytes")
        self.contract = json.loads(raw)
        if set(self.contract["tools"]) != CORE_TOOLS:
            raise ValueError("Unexpected commerce tool set")
        # MCP1.28 already requires this package. Never install it implicitly.
        from jsonschema import Draft202012Validator, validators

        strict = Draft202012Validator.TYPE_CHECKER.redefine(
            "integer", lambda _checker, value: type(value) is int
        ).redefine("number", lambda _checker, value:
                   type(value) in (int, float) and math.isfinite(value))
        validator = validators.extend(Draft202012Validator, type_checker=strict)
        self.validators = {}
        for tool, schemas in self.contract["tools"].items():
            for direction in ("input", "output"):
                schema = schemas[direction + "Schema"]
                validator.check_schema(schema)
                self.validators[tool, direction] = validator(schema)

    def __call__(self, tool: str, direction: str, value: dict) -> None:
        validator = self.validators.get((tool, direction))
        if validator is None:
            raise ValueError("Unknown commerce schema")
        if next(validator.iter_errors(value), None) is not None:
            raise ValueError("Commerce schema refused the value")
        if direction == "input" and "lines" in value:
            ids = [line["product_id"] for line in value["lines"]]
            if len(ids) != len(set(ids)):
                raise ValueError("Duplicate products")
        if direction == "output" and value["data"]["ok"]:
            data = value["data"]
            if (data["state"] == "pending") != (data["projection"] == "pending"):
                raise ValueError("Inconsistent projection phase")

    def check_remote_tools(self, tools) -> None:
        """Require the initialized MCP1.28 session's actual advertised schemas."""
        if len(tools) != len(CORE_TOOLS) or {tool.name for tool in tools} != CORE_TOOLS:
            raise ValueError("Unexpected remote tools")
        for tool in tools:
            expected = self.contract["tools"][tool.name]
            actual = {"inputSchema": tool.inputSchema, "outputSchema": tool.outputSchema}
            if canonical(actual) != canonical(expected):
                raise ValueError("Remote commerce schemas changed")
