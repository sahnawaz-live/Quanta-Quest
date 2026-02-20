"""Asset path resolution for Quanta Quest."""

from pathlib import Path

_ASSETS_DIR = Path(__file__).parent


def asset_path(name: str) -> str:
    """Return the absolute path to a game asset file."""
    return str(_ASSETS_DIR / name)
