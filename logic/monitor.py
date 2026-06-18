import json
import os
from enum import Enum
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MONITOR_FILE = os.path.join(
    BASE_DIR,
    "data",
    "monitor_state.json"
)





def _serialize(value):

    if isinstance(value, Enum):
        return value.name

    if isinstance(value, set):
        return list(value)

    return value


def update_monitor(**kwargs):

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