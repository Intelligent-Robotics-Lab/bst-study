import requests
import json

class Feedback:
    def __init__(self, agent):
        self.agent = agent

OLLAMA_URL = "http://localhost:11434/api/chat"

SYSTEM_PROMPT = """
You are a behavioral fidelity evaluator for Discrete Trial Training (DTT).

You evaluate teaching sessions based on:
- instruction delivery
- prompting accuracy
- reinforcement correctness
- error correction

Rules:
- Only use the provided event log.
- Do NOT guess missing information.
- Be strict and consistent.
- You are NOT evaluating the child ONLY the trainer
"""

def evaluate_dtt_session(event_log, model="llama3.1:8b"):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(event_log)}
        ],
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code != 200:
        raise Exception(f"Ollama error: {response.text}")

    result = response.json()

    return result["message"]["content"]


if __name__ == "__main__":
    sample_session = {
        "trial_id": 1,
        "events": [
            {"t": 0.0, "type": "SD", "content": "touch nose"},
            {"t": 1.0, "type": "response", "content": "touched ear", "correct": False},
            {"t": 2.0, "type": "prompt", "level": "verbal"},
            {"t": 3.0, "type": "response", "content": "touched nose", "correct": True},
            {"t": 3.5, "type": "reinforcement", "delivered": True}
        ]
    }

    output = evaluate_dtt_session(sample_session)
    print(output)