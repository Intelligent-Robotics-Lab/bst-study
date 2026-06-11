from flask import Flask, jsonify, render_template
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MONITOR_FILE = os.path.join(
    BASE_DIR,
    "data",
    "monitor_state.json"
)

print(f"[WEBPAGE] Using monitor file: {MONITOR_FILE}")

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/current_sd")
def current_sd():

    try:
        with open(MONITOR_FILE, "r") as f:
            data = json.load(f)

        print(f"[FLASK READ] {data}")

        return jsonify({
            "screen": data.get("screen", "rehearsal"),
            "current_phase": data.get("current_phase", 0),

            "trial_sd": data.get("trial_sd"),
            "trial_state": data.get("trial_state"),
            "transcript": data.get("transcript"),
            "emotion": data.get("emotion"),

            "completed_sds": data.get("completed_sds", [])
        })

    except Exception as e:

        print(f"[MONITOR ERROR] {e}")

        return jsonify({
            "screen": "rehearsal",
            "current_phase": 0,

            "trial_sd": None,
            "trial_state": None,
            "transcript": None,
            "emotion": None,

            "completed_sds": []
        })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )