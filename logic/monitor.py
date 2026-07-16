import json
import os
from enum import Enum

import requests

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MONITOR_FILE = os.path.join(
    BASE_DIR,
    "data",
    "monitor_state.json"
)

# Data-collection platform. The participant tablet (served by the platform) shows
# the live Current SD + Trial State, so we mirror monitor_state to the platform.
PLATFORM_BASE = os.getenv("BST_PLATFORM_BASE", "http://141.210.88.210:8080")

def _serialize(value):
    """Serializes a value for JSON storage. Handles special cases for Enums and sets."""
    if isinstance(value, Enum):
        return value.name

    if isinstance(value, set):
        return list(value)

    return value


def update_monitor(**kwargs):
    """Updates the monitor state JSON file with the provided keyword arguments."""
    print("[MONITOR UPDATE]", kwargs)

    try:
        with open(MONITOR_FILE, "r") as f:
            data = json.load(f)

    except Exception:
        data = {}

    serialized = {
        key: _serialize(value)
        for key, value in kwargs.items()
    }

    data.update(serialized)

    with open(MONITOR_FILE, "w") as f:
        json.dump(data, f, indent=2)

    # Mirror the state to the data-collection platform so the participant tablet
    # can show the live Current SD + Trial State. Fire-and-forget: this is UI
    # mirroring, never control flow, so a platform hiccup must not break the run.
    try:
        requests.post(f"{PLATFORM_BASE}/monitor", json=data, timeout=2)
    except Exception as exc:  # noqa: BLE001
        print(f"[MONITOR] platform mirror failed (continuing): {exc}")