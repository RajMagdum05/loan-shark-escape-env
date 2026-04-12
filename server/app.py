"""
OpenEnv entry shim: ``openenv.yaml`` and tools expect ``server.app:app``.

The real ASGI application lives in the repo root ``app.py`` (single source of truth).
"""
from __future__ import annotations

from app import app

__all__ = ["app"]
