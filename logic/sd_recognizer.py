import json
import requests


class SDRecognizer:
    """
    Maps observed multimodal input (speech + optional behavior text)
    to SD_X entries in your DTT trial_data.

    Outputs:
    - SD ID match
    - confidence
    - semantic + emotional interpretation
    """

    def __init__(self, trial_data, model="llama3.1"):
        self.trial_data = trial_data["trial_data"] # Fix this compile error
        self.model = model
        self.url = "http://localhost:11434/api/chat"

    # -----------------------------
    # PUBLIC ENTRY POINT
    # -----------------------------
    def recognize(self, observed_input: dict):
        """
        observed_input example:
        {
            "verbal_text": "...",
            "nonverbals": {... optional ...}
        }
        """

        candidates = self._build_candidate_map()

        prompt = self._build_prompt(observed_input, candidates)

        response = self._call_llm(prompt)

        parsed = self._safe_parse(response)

        # Attach resolved SD data
        sd_id = parsed.get("matched_sd_id")
        parsed["resolved_sd"] = self.trial_data.get(sd_id, None)

        return parsed

    # -----------------------------
    # BUILD CANDIDATES FROM YOUR SCHEMA
    # -----------------------------
    def _build_candidate_map(self):
        candidates = {}

        for sd_id, sd in self.trial_data.items():
            candidates[sd_id] = {
                "sd": sd["sd"],
                "sd_type": sd["sd_type"],
                "object": sd.get("object"),
                "action": sd.get("action"),
                "emotion": sd.get("emotion")
            }

        return candidates

    # -----------------------------
    # PROMPT ENGINEERING
    # -----------------------------
    def _build_prompt(self, observed_input, candidates):
        return f"""
You are an SD recognizer for a DTT (Discrete Trial Training) system.

Your job is to match an observed learner response to the correct SD entry.

You must:
1. Match based on meaning, not exact wording
2. Consider SD type (Manding, Imitation, Labeling, Emotion, Reception)
3. Extract object/action/emotion if present
4. Return ONLY valid JSON

---

OBSERVED INPUT:
{json.dumps(observed_input, indent=2)}

---

CANDIDATE SDs:
{json.dumps(candidates, indent=2)}

---

RETURN FORMAT (STRICT):
{{
  "matched_sd_id": "SD_1",
  "confidence": 0.0 to 1.0,

  "match_type": "exact | paraphrase | expanded | partial | unclear",

  "interpretation": {{
    "intent": "string (e.g. manding, imitation, labeling, emotion, reception)",
    "object": "string or null",
    "action": "string or null",
    "emotion": "string or null"
  }},

  "reasoning_brief": "short explanation"
}}
"""

    # -----------------------------
    # OLLAMA CALL
    # -----------------------------
    def _call_llm(self, prompt):
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a strict structured-output JSON system. Output ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False
        }

        r = requests.post(self.url, json=payload)

        return r.json()["message"]["content"]

    # -----------------------------
    # SAFE JSON PARSE
    # -----------------------------
    def _safe_parse(self, text):
        try:
            return json.loads(text)
        except Exception:
            # fallback if model adds extra text
            start = text.find("{")
            end = text.rfind("}")
            return json.loads(text[start:end])