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
            return jsonify(json.load(f))

    except Exception:
        return jsonify({
            "trial_sd": None,
            "trial_state": None
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)