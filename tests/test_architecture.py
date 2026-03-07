"""Architectural compliance tests for Deepthought Ed-OS mandates."""

from pathlib import Path

import pytest
from dt_testing.arch import check_file_compliance


@pytest.mark.architecture
@pytest.mark.parametrize("folder", ["src", "tests"])
def test_architectural_ratchet(folder: str) -> None:
    """Verify that all files in the folder comply with architectural mandates."""
    member_root = Path(__file__).parent.parent
    target_dir = member_root / folder

    if not target_dir.exists():
        return

    all_errors = []
    for p in target_dir.rglob("*.py"):
        if p.name in {"test_architecture.py", "__init__.py"}:
            continue
        errors = check_file_compliance(p)
        if errors:
            all_errors.append(f"\n{p.relative_to(member_root.parent)}:" + "\n".join(errors))

    if all_errors:
        pytest.fail("Architectural compliance failed:" + "".join(all_errors))
