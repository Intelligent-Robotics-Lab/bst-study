import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MONITOR_FILE = os.path.join(
    BASE_DIR,
    "data",
    "monitor_state.json"
)

def update_monitor(**kwargs):
    print("[MONITOR UPDATE]", kwargs)

    try:
        with open(MONITOR_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}

    data.update(kwargs)

    with open(MONITOR_FILE, "w") as f:
        json.dump(data, f, indent=2)