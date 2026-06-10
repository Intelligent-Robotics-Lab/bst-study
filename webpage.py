from flask import Flask, jsonify, render_template
import json

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/current_sd")
def current_sd():

    try:
        with open("monitor_state.json", "r") as f:
            data = json.load(f)

        return jsonify({
            "trial_sd": data.get("trial_sd"),
            "trial_state": data.get("trial_state"),
            "transcript": data.get("transcript"),
            "emotion": data.get("emotion"),
            "completed_sds": data.get("completed_sds", [])
        })

    except Exception as e:
        print(e)

        return jsonify({
            "trial_sd": None,
            "trial_state": None,
            "transcript": None,
            "emotion": None,
            "completed_sds": []
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)