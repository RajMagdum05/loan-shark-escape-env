"""
Re-export the FastAPI app so both work:

  uvicorn server.app:app   # openenv.yaml / Dockerfile
  uvicorn app:app          # alternate HF / local convention
"""

from server.app import app

__all__ = ["app"]
