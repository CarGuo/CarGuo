import hashlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.mark.skipif(
    not (REPO_ROOT / "dark_mode.svg").exists() or not (REPO_ROOT / ".regression").exists(),
    reason="regression baseline not pinned yet",
)
def test_svg_hashes_match_baseline():
    """Rerun `make update` locally, then pin baseline with:

        python -c "import hashlib,pathlib; \\
          root=pathlib.Path('.'); \\
          (root/'.regression').write_text( \\
              'dark_mode.svg=' + \\
              hashlib.sha256((root/'dark_mode.svg').read_bytes()).hexdigest() + '\\n')"

    Any layout regression will then fail this test.
    """
    baseline = {}
    for line in (REPO_ROOT / ".regression").read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            baseline[k.strip()] = v.strip()
    for name, expected in baseline.items():
        actual = _sha256(REPO_ROOT / name)
        assert actual == expected, f"{name} hash drifted: {actual} != {expected}"
