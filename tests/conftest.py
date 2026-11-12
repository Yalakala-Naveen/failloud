"""Make the test suite runnable from a fresh clone without installing.

If ``failloud`` is already installed (the normal case, ``pip install -e .``)
this does nothing. Otherwise it puts ``src/`` on ``sys.path`` so
``python -m pytest`` works out of the box.
"""

import sys
from pathlib import Path

try:
    import failloud  # noqa: F401
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
