from sentence_transformers import SentenceTransformer
import numpy as np


class SDRecognizer:

    def __init__(self, trial_data, threshold=0.35):
        self.trial_data = trial_data
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # Minimum level of similarity required to trigger the SD
        self.threshold = threshold

        self.sd_ids = []
        self.sd_embeddings = []

        for sd_id, sd in trial_data.items():
            text = self._build_sd_text(sd)
            embedding = self.model.encode(text)

            self.sd_ids.append(sd_id)
            self.sd_embeddings.append(embedding)

    def _build_sd_text(self, sd):
        parts = [
            sd.get("sd", ""),
            sd.get("sd_type", ""),
            sd.get("object", "") or "",
            sd.get("action", "") or "",
        ]
        return " ".join(parts)

    def recognize(self, observed_input: dict):

        query = self._build_query(observed_input)
        query_emb = self.model.encode(query)

        detected_emotion = (observed_input.get("emotion") or "").lower()
        print("Detected emotion:", repr(detected_emotion))
        scores = []

        for i, sd_emb in enumerate(self.sd_embeddings):

            sd_id = self.sd_ids[i]
            sd = self.trial_data[sd_id]
            score = self._cosine(query_emb, sd_emb)
            scores.append((score, sd_id))

        if not scores:
            return {
                "matched_sd_id": None,
                "confidence": 0.0,
                "resolved_sd": None,
                "rejected": True
            }

        scores.sort(reverse=True)

        best_score, best_sd = scores[0]

        if best_score < self.threshold:
            return {
                "matched_sd_id": None,
                "confidence": float(best_score),
                "resolved_sd": None,
                "rejected": True
            }

        return {
            "matched_sd_id": best_sd,
            "confidence": float(best_score),
            "resolved_sd": self.trial_data[best_sd],
            "rejected": False
        }

    def _build_query(self, observed):
        return f"{observed.get('verbal_text','')}"

    def _cosine(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))