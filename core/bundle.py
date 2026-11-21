"""Monthly data bundle: how Lumino's numbers reach the app without living in the repo.

The raw files stay on the build laptop. `tools/make_bundle.py` sums them to month x item x godown
and packs the result into one text blob. The app finds that blob in, in this order:

1. Streamlit secrets (`LUMINO_BUNDLE`)  - how the deployed app gets it
2. the `LUMINO_BUNDLE` environment variable
3. `data_local/bundle.txt`              - local development (git-ignored)

Nothing readable is committed. Without the blob the app says so instead of crashing.
"""

from __future__ import annotations

import base64
import io
import json
import os
import zlib
from pathlib import Path

import pandas as pd

BUNDLE_VERSION = 1
LOCAL_FILE = Path(__file__).resolve().parent.parent / "data_local" / "bundle.txt"


def pack(tables: dict[str, pd.DataFrame]) -> str:
    payload = {name: df.to_csv(index=False) for name, df in tables.items()}
    raw = json.dumps({"v": BUNDLE_VERSION, "tables": payload}, separators=(",", ":")).encode()
    return base64.b64encode(zlib.compress(raw, 9)).decode()


def unpack(blob: str) -> dict[str, pd.DataFrame]:
    data = json.loads(zlib.decompress(base64.b64decode(blob.strip())))
    if data.get("v") != BUNDLE_VERSION:
        raise ValueError("Data bundle has an unexpected version")
    return {name: pd.read_csv(io.StringIO(csv)) for name, csv in data["tables"].items()}


def find_blob() -> str | None:
    """Look for the bundle in secrets, then the environment, then the local file."""
    try:
        import streamlit as st

        blob = st.secrets.get("LUMINO_BUNDLE")
        if blob:
            return str(blob)
    except Exception:
        pass
    blob = os.environ.get("LUMINO_BUNDLE")
    if blob:
        return blob
    if LOCAL_FILE.exists():
        return LOCAL_FILE.read_text(encoding="utf-8")
    return None


def load_tables() -> dict[str, pd.DataFrame] | None:
    blob = find_blob()
    return unpack(blob) if blob else None
