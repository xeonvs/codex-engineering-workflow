from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skill" / "engineering-workflow" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def load_script_module(name: str):
    path = SCRIPT_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
