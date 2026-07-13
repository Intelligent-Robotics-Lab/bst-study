from sentence_transformers import SentenceTransformer
import numpy as np


class SDRecognizer:
    """Recognizes discriminative stimuli (SDs) based on observed input using sentence embeddings and semantic similarity."""
    def __init__(self, trial_data, threshold=0.35):
        self.trial_data = trial_data
        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        self.threshold = threshold

        self.sd_ids = []
        self.sd_embeddings = []

        for utterance_id, utterance in trial_data.items():
            text = self._build_sd_text(
                utterance
            )
            embedding = self.model.encode(
                text
            )

            self.sd_ids.append(
                utterance_id
            )
            self.sd_embeddings.append(
                embedding
            )

    def _build_sd_text(self, utterance):
        return utterance.get(
            "text",
            ""
        )

    def recognize(
        self,
        observed_input: dict
    ):

        query = self._build_query(
            observed_input
        )
        query_emb = self.model.encode(
            query
        )

        detected_emotion = (
            observed_input.get(
                "emotion"
            )
            or ""
        ).lower()

        print(
            "Detected emotion:",
            repr(detected_emotion)
        )

        scores = []

        for i, emb in enumerate(
            self.sd_embeddings
        ):
            utterance_id = (
                self.sd_ids[i]
            )

            score = self._cosine(
                query_emb,
                emb
            )

            scores.append(
                (
                    score,
                    utterance_id,
                )
            )

        if not scores:
            return {
                "matched_sd_id": None,
                "matched_type": None,
                "confidence": 0.0,
                "resolved_sd": None,
                "rejected": True,
            }

        scores.sort(
            reverse=True
        )

        (
            best_score,
            best_id,
        ) = scores[0]

        if (
            best_score
            < self.threshold
        ):
            return {
                "matched_sd_id": None,
                "matched_type": None,
                "confidence": float(
                    best_score
                ),
                "resolved_sd": None,
                "rejected": True,
            }

        resolved = self.trial_data[
            best_id
        ]

        return {
            "matched_sd_id": best_id,
            "matched_type": resolved.get(
                "type"
            ),
            "confidence": float(
                best_score
            ),
            "resolved_sd": resolved,
            "rejected": False,
        }

    def _build_query(
        self,
        observed
    ):
        return observed.get(
            "verbal_text",
            "",
        )

    def _cosine(
        self,
        a,
        b,
    ):
        return np.dot(
            a,
            b,
        ) / (
            np.linalg.norm(a)
            * np.linalg.norm(b)
        )