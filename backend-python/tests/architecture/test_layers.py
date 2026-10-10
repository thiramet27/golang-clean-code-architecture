import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clean_architecture_dependency_rule() -> None:
    """Contracts live in pyproject.toml ([tool.importlinter]): inner layers never import outer ones."""
    result = subprocess.run(
        [str(Path(sys.executable).parent / "lint-imports"), "--config", str(ROOT / "pyproject.toml")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
