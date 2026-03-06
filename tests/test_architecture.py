import re
from pathlib import Path


def test_no_noqa_or_type_ignore() -> None:
    """Verify that no # noqa or # type: ignore comments exist in the codebase."""
    forbidden = ["noqa", "type: ignore"]
    src_dir = Path("src")
    tests_dir = Path("tests")

    files_to_check = list(src_dir.rglob("*.py")) + list(tests_dir.rglob("*.py"))

    violations = []
    for file_path in files_to_check:
        if file_path.name == "test_architecture.py":
            continue
        content = file_path.read_text()
        for i, line in enumerate(content.splitlines(), 1):
            if any(f in line for f in forbidden):
                violations.append(f"{file_path}:{i}: Found forbidden comment in line: {line}")

    assert not violations, "\n".join(violations)

def test_zero_any() -> None:
    """Verify that the literal 'Any' is not used in the codebase."""
    any_pattern = r"\bAny\b"
    allowed_marker = "# architectural: allowed-object"
    src_dir = Path("src")
    tests_dir = Path("tests")

    files_to_check = list(src_dir.rglob("*.py")) + list(tests_dir.rglob("*.py"))

    violations = []
    for file_path in files_to_check:
        if file_path.name == "test_architecture.py":
            continue
        content = file_path.read_text()
        for i, line in enumerate(content.splitlines(), 1):
            # Ignore imports of Any
            if line.strip().startswith(("import ", "from ")):
                continue
            if re.search(any_pattern, line) and allowed_marker not in line:
                violations.append(f"{file_path}:{i}: Forbidden use of 'Any' in line: {line}")

    assert not violations, "\n".join(violations)
def test_object_sovereignty() -> None:
    """Verify that 'object' as a type is only used with justification."""
    object_pattern = r":\s*object\b"
    allowed_marker = "# architectural: allowed-object"
    src_dir = Path("src")
    tests_dir = Path("tests")

    files_to_check = list(src_dir.rglob("*.py")) + list(tests_dir.rglob("*.py"))

    violations = []
    for file_path in files_to_check:
        content = file_path.read_text()
        for i, line in enumerate(content.splitlines(), 1):
            if re.search(object_pattern, line) and allowed_marker not in line:
                violations.append(f"{file_path}:{i}: Forbidden use of 'object' as type without justification: {line}")

    assert not violations, "\n".join(violations)
