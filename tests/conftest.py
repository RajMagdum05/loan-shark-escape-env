import sys
from pathlib import Path

import pytest

# Repo root on path for `import models`, `import server`
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@pytest.fixture
def no_random_shocks(monkeypatch):
    """Disable income/medical shocks so tests are deterministic."""
    monkeypatch.setattr("server.environment.random.random", lambda: 1.0)
