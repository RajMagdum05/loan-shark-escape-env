"""
OpenEnv entry shim: ``openenv.yaml`` and tools expect ``server.app:app``.

The real ASGI application lives in the repo root ``app.py`` (single source of truth).
"""
from __future__ import annotations

from app import app

__all__ = ["app"]


def main() -> None:
    """CLI entry for ``uv run server`` / ``python -m server.app`` (multi-mode deploy)."""
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
