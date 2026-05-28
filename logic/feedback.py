import json
import os
import re
import time
from typing import Any

import requests
from dotenv import load_dotenv

# =====================================================
# IRL2LLM CONFIGURATION
# =====================================================

load_dotenv()

IRL2LLM_URL = os.getenv(
    "IRL2LLM_URL",
    "http://141.210.88.210:8015",
)

IRL2LLM_API_KEY = os.getenv("IRL2LLM_API_KEY")

DEFAULT_MODEL = os.getenv(
    "LOCAL_LLM_MODEL",
    "llama3.3:70b",
)

# =====================================================
# SYSTEM PROMPT
# =====================================================

SYSTEM_PROMPT = """
You are evaluating trainer fidelity in a DTT session.

IMPORTANT:
The DTT engine has ALREADY determined:
- the trial type
- the child response
- the required trainer actions

Your ONLY task is to evaluate whether the trainer:
1. Performed the required actions
2. Performed them in the correct order
3. Used appropriate trainer behavior
4. Delivered reinforcement appropriately

DO NOT:
- infer child behavior
- infer protocol requirements
- invent missing requirements
- penalize optional strategies

Evaluate ONLY against:
- expected trainer sequence
- observed trainer behavior

Return ONLY valid JSON matching this schema:

{
  "overall_score": int,
  "sd_score": int,
  "prompt_score": int,
  "reinforcement_score": int,
  "sequencing_score": int,
  "error_correction_score": int,
  "strengths": [str],
  "improvements": [str],
  "protocol_violations": [str],
  "number_of_failed": int,
  "feedback_statement": str
}

IMPORTANT:
The interaction_history contains ALL trainer speech attempts,
including:
- failed attempts
- corrected attempts
- retries
- reformulations

Use this history to evaluate:
- whether the trainer corrected mistakes
- whether corrections improved clarity
- whether prompting improved over time
- whether recovery procedures were appropriate

IMPORTANT SCORING RULES:

- The trainer should be penalized for failed attempts,
  even if they later recover successfully.

- Multiple attempts reduce fidelity compared to a correct
  first attempt.

- Successful recovery is better than persistent failure,
  but should NOT receive a perfect score.

- If interaction_history shows failed attempts before a
  successful attempt, reduce relevant scores appropriately.

- First-attempt correctness should score higher than
  corrected performance.

Give the participant the feedback directly and address them as Carter
"""

# =====================================================
# FEEDBACK HOLDER
# =====================================================


class FeedbackHolder:

    def __init__(self):
        self.reset()

    def reset(self):

        self.trial_id = None

        # Determined by DTT engine/state machine
        self.trial_context = {
            "trial_type": None,
            "child_response": None,
            "expected_trainer_sequence": [],
        }

        self.trainer_events = []
        self.interaction_history = []

    # =====================================================
    # TRAINER EVENT RECORDING
    # =====================================================

    def add_trainer_event(
        self,
        event_type: str,
        text: str,
        t: float | None = None,
    ):

        self.trainer_events.append(
            {
                "type": event_type,
                "text": text,
                "time": (
                    t
                    if t is not None
                    else time.time()
                ),
            }
        )
    def add_transcript_event(
        self,
        trial_state,
        text,
        recognized_as=None,
        successful=False,
    ):

        if not hasattr(self, "interaction_history"):
            self.interaction_history = []

        self.interaction_history.append({
            "trial_state": str(trial_state),
            "text": text,
            "recognized_as": recognized_as,
            "successful": successful,
            "corrected_later": False,
        })
    # =====================================================
    # ACTUAL TRAINER SEQUENCE
    # =====================================================

    def get_actual_sequence(self):

        ordered_events = sorted(
            self.trainer_events,
            key=lambda x: x["time"],
        )

        return [
            event["type"]
            for event in ordered_events
        ]

    # =====================================================
    # ORDER VALIDATION
    # =====================================================

    @staticmethod
    def sequence_score(
        expected_sequence,
        actual_sequence,
    ):

        if not expected_sequence:
            return 100

        idx = 0

        for item in actual_sequence:

            if (
                idx < len(expected_sequence)
                and item == expected_sequence[idx]
            ):
                idx += 1

        return int(
            (idx / len(expected_sequence)) * 100
        )

    # =====================================================
    # RULE-BASED PRELIMINARY SCORING
    # =====================================================

    def compute_preliminary_scores(self):

        expected_sequence = self.trial_context[
            "expected_trainer_sequence"
        ]

        actual_sequence = self.get_actual_sequence()

        trainer_types = set(actual_sequence)

        # ==========================================
        # DETECTIONS
        # ==========================================

        sd_detected = "sd" in trainer_types

        prompt_detected = (
            "prompt" in trainer_types
        )

        reinforcement_detected = (
            "reinforcement" in trainer_types
        )

        hp_detected = (
            "high_probability_sd"
            in trainer_types
        )

        retry_detected = (
            "retry_sd"
            in trainer_types
        )

        # ==========================================
        # EXPECTATION DETECTION
        # ==========================================

        prompt_expected = (
            "prompt" in expected_sequence
        )

        reinforcement_expected = (
            "reinforcement"
            in expected_sequence
        )

        hp_expected = (
            "high_probability_sd"
            in expected_sequence
        )

        retry_expected = (
            "retry_sd"
            in expected_sequence
        )

        # ==========================================
        # INDIVIDUAL SCORES
        # ==========================================

        sd_score = (
            100
            if sd_detected
            else 0
        )

        prompt_score = 100

        if prompt_expected:
            prompt_score = (
                100
                if prompt_detected
                else 0
            )

        reinforcement_score = 100

        if reinforcement_expected:
            reinforcement_score = (
                100
                if reinforcement_detected
                else 0
            )

        error_correction_score = 100

        if hp_expected and not hp_detected:
            error_correction_score -= 50

        if retry_expected and not retry_detected:
            error_correction_score -= 50

        error_correction_score = max(
            0,
            error_correction_score,
        )

        sequencing_score = self.sequence_score(
            expected_sequence,
            actual_sequence,
        )

        overall_score = int(
            (
                sd_score
                + prompt_score
                + reinforcement_score
                + sequencing_score
                + error_correction_score
            )
            / 5
        )

        return {
            "sd_score": sd_score,
            "prompt_score": prompt_score,
            "reinforcement_score": reinforcement_score,
            "sequencing_score": sequencing_score,
            "error_correction_score": (
                error_correction_score
            ),
            "overall_preliminary_score": (
                overall_score
            ),
            "actual_sequence": actual_sequence,
        }

    # =====================================================
    # BUILD PAYLOAD
    # =====================================================

    def build_evaluation_payload(
        self,
    ) -> dict[str, Any]:

        ordered_events = sorted(
            self.trainer_events,
            key=lambda x: x["time"],
        )

        preliminary_scores = (
            self.compute_preliminary_scores()
        )

        recovery_metrics = (
            self.compute_recovery_metrics()
        )

        return {
            "trial_id": self.trial_id,

            "trial_context": self.trial_context,

            "precomputed_analysis": (
                preliminary_scores
            ),

            "trainer_behavior": (
                ordered_events
            ),

            "interaction_history": (
                self.interaction_history
            ),
            "recovery_metrics": recovery_metrics,
        }

    def compute_recovery_metrics(self):

        failed_attempts = 0
        corrected_attempts = 0

        for event in self.interaction_history:

            if not event["successful"]:
                failed_attempts += 1

            if event["corrected_later"]:
                corrected_attempts += 1

        recovery_ratio = 1.0

        if failed_attempts > 0:

            recovery_ratio = (
                corrected_attempts
                / failed_attempts
            )

        return {
            "failed_attempts": failed_attempts,
            "corrected_attempts": corrected_attempts,
            "recovery_ratio": recovery_ratio,
        }

# =====================================================
# JSON EXTRACTION
# =====================================================


def extract_json(
    text: str,
) -> str | None:

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL,
    )

    return (
        match.group(0)
        if match
        else None
    )


# =====================================================
# IRL2LLM CHAT
# =====================================================


def call_irl2llm_chat(
    messages: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    max_context_tokens: int = 4096,
    timeout: int = 300,
) -> str:

    if not IRL2LLM_API_KEY:

        raise RuntimeError(
            "IRL2LLM_API_KEY is not set."
        )

    response = requests.post(
        f"{IRL2LLM_URL}/chat",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": IRL2LLM_API_KEY,
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_context_tokens": (
                max_context_tokens
            ),
        },
        timeout=timeout,
    )

    if response.status_code != 200:

        raise RuntimeError(
            f"irl2llm request failed "
            f"with status "
            f"{response.status_code}: "
            f"{response.text}"
        )

    result = response.json()

    if "response" not in result:

        raise RuntimeError(
            f"Unexpected response format: "
            f"{result}"
        )

    return result["response"]


# =====================================================
# DTT SESSION EVALUATION
# =====================================================


def evaluate_dtt_session(
    event_log: dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": json.dumps(
                event_log,
                indent=2,
            ),
        },
    ]

    content = call_irl2llm_chat(
        messages=messages,
        model=model,
        temperature=0.2,
        max_context_tokens=4096,
        timeout=300,
    )

    print("\n===== RAW LLM OUTPUT =====")
    print(content)

    json_text = extract_json(content)

    if not json_text:

        raise RuntimeError(
            "No valid JSON object "
            "returned by model."
        )

    try:

        return json.loads(json_text)

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            f"Model returned invalid JSON: "
            f"{exc}\n\n"
            f"RAW OUTPUT:\n{content}"
        )


# =====================================================
# OPTIONAL TEST
# =====================================================

if __name__ == "__main__":

    holder = FeedbackHolder()

    holder.trial_id = "trial_001"

    # ==========================================
    # PROVIDED BY DTT ENGINE
    # ==========================================

    holder.trial_context = {
        "trial_type": "error_correction",

        "child_response": "no_response",

        "expected_trainer_sequence": [
            "sd",
            "prompt",
            "reinforcement",
        ],
    }

    # ==========================================
    # TEST EVENTS
    # ==========================================

    base = time.time()

    holder.add_trainer_event(
        "sd",
        "Do this: clap hands",
        base + 0.0,
    )

    holder.add_trainer_event(
        "prompt",
        "Clap hands like this",
        base + 1.0,
    )

    holder.add_trainer_event(
        "reinforcement",
        "Great job clapping!",
        base + 2.0,
    )

    # ==========================================
    # BUILD PAYLOAD
    # ==========================================

    event_log = (
        holder.build_evaluation_payload()
    )

    print("\n===== EVENT LOG =====")

    print(
        json.dumps(
            event_log,
            indent=2,
        )
    )

    # ==========================================
    # EVALUATE
    # ==========================================

    result = evaluate_dtt_session(
        event_log
    )

    print("\n===== PARSED EVALUATION =====")

    print(
        json.dumps(
            result,
            indent=2,
        )
    )