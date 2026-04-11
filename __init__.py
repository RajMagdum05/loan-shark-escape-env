"""Loan Shark Escape package exports."""

from typing import Any

from .models import LoanSharkAction, LoanSharkObservation

__all__ = [
    "LoanSharkAction",
    "LoanSharkObservation",
    "LoanSharkEscapeEnv",
]


def __getattr__(name: str) -> Any:
    if name == "LoanSharkEscapeEnv":
        from .client import LoanSharkEscapeEnv as _LoanSharkEscapeEnv

        return _LoanSharkEscapeEnv
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
