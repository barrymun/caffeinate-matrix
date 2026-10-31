"""Shared helpers for the caffeinate-matrix tests."""

import importlib.machinery
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "caffeinate-matrix"


def load_script():
    """Import the script as a module (it has no .py extension, so a plain
    import won't find it)."""
    loader = importlib.machinery.SourceFileLoader("caffeinate_matrix", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module
