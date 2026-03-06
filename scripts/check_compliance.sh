#!/bin/bash
set -e

echo "--- Scanning for Compliance Violations (# noqa, type: ignore) ---"
VIOLATIONS=$(grep -rE --include="*.py" "noqa|type:\s*ignore" src tests | grep -v "scripts/check_compliance.sh" | grep -v "tests/test_architecture.py" || true)

if [ -n "$VIOLATIONS" ]; then
    echo "ERROR: Forbidden usage of # noqa or # type: ignore detected:"
    echo "$VIOLATIONS"
    exit 1
fi

echo "--- Architectural Ratchet (Zero-Any) ---"
# Check for Any, but allow it if the line or preceding line has the marker
# Also allow it in imports and in test_architecture.py
ANY_VIOLATIONS=$(grep -rE --include="*.py" "\bAny\b" src tests \
    | grep -v "from typing import" \
    | grep -v "import typing" \
    | grep -v "tests/test_architecture.py" \
    | grep -v "# architectural: allowed-object" || true)

if [ -n "$ANY_VIOLATIONS" ]; then
    echo "ERROR: Literal 'Any' is banned in production and test code:"
    echo "$ANY_VIOLATIONS"
    exit 1
fi

echo "--- Architectural Ratchet (Object Sovereignty) ---"
# Check for 'object' as a type, but allow it if tagged
OBJECT_VIOLATIONS=$(grep -rE --include="*.py" ":\s*object\b" src tests | grep -v "# architectural: allowed-object" || true)

if [ -n "$OBJECT_VIOLATIONS" ]; then
    echo "ERROR: Use of 'object' as a type is prohibited without justification:"
    echo "$OBJECT_VIOLATIONS"
    exit 1
fi

echo "SUCCESS: Compliance check passed."
