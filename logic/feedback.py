import json
import os
import re
import time
from typing import Any

import requests
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from datetime import datetime
import json

SAVE_EVALUATION_DATA = False
# =====================================================
# IRL2LLM CONFIGURATION
# =====================================================

load_dotenv()

#IRL2LLM_URL = os.getenv(
#    "IRL2LLM_URL",
#    "http://141.210.88.210:8015",
#)

#IRL2LLM_API_KEY = os.getenv("IRL2LLM_API_KEY")

#DEFAULT_MODEL = os.getenv(
#    "LOCAL_LLM_MODEL",
#    "llama3.3:70b",
#)


OPENAI_API_KEY = os.getenv("OPENAI_KEY", "").strip()

DEFAULT_MODEL = "gpt-5.4-mini"
client = OpenAI(
    api_key=OPENAI_API_KEY
)
# =====================================================
# SYSTEM PROMPT
# =====================================================



# =====================================================
# FEEDBACK HOLDER
# =====================================================


class FeedbackHolder:

    def __init__(self, study_config =None):
        self.reset()
        self.study_config = study_config

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
    # =====================================================
    # ERROR CLASSIFICATION
    # =====================================================

    def classify_event(
        self,
        trial_state,
        text,
        recognized_as=None,
        successful=False,
        result_type="success",
    ):
        """
        Classification is determined upstream by the
        DTT engine / recognition handlers.

        This method simply records the result.
        """

        state = str(trial_state)

        if result_type == "success":
            return

        if result_type == "uncertain":

            self.uncertain_events.append(
                {
                    "state": state,
                    "reason": "recognition_failed",
                    "text": text,
                    "recognized_as": recognized_as,
                }
            )

            return

        if result_type == "confirmed_error":

            self.confirmed_errors.append(
                {
                    "state": state,
                    "observed": recognized_as,
                    "text": text,
                }
            )

            return


    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.trial_id = None

        self.trial_context = {
            "trial_type": None,
            "child_response": None,
            "expected_trainer_sequence": [],
        }

        self.trainer_events = []
        self.interaction_history = []

        # NEW
        self.confirmed_errors = []
        self.uncertain_events = []


    # =====================================================
    # TRANSCRIPT EVENT RECORDING
    # =====================================================

    def add_transcript_event(
        self,
        trial_state,
        text,
        recognized_as=None,
        successful=False,
        result_type="success",
    ):

        if not hasattr(
            self,
            "interaction_history",
        ):
            self.interaction_history = []

        event = {
            "trial_state": str(trial_state),
            "text": text,
            "recognized_as": recognized_as,
            "successful": successful,
            "result_type": result_type,
            "corrected_later": False,
        }

        self.interaction_history.append(
            event
        )

        self.classify_event(
            trial_state=trial_state,
            text=text,
            recognized_as=recognized_as,
            successful=successful,
            result_type=result_type,
        )

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

            "trial_context":
                self.trial_context,

            "precomputed_analysis":
                preliminary_scores,

            "trainer_behavior":
                ordered_events,

            "interaction_history":
                self.interaction_history,

            # NEW
            "confirmed_errors":
                self.confirmed_errors,

            # NEW
            "uncertain_events":
                self.uncertain_events,

            "recovery_metrics":
                recovery_metrics,
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

def call_openai_chat(
    messages: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
) -> str:


    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
    )


    return response.choices[0].message.content
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
def save_evaluation_snapshot(
    event_log: dict,
    study_config: dict,
    result: dict | None = None,
):
    """
    Saves everything the feedback system used to generate feedback.

    Can be replayed later against new prompts.
    """

    if not SAVE_EVALUATION_DATA:
        return

    Path("feedback_training_data").mkdir(
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    trial_id = event_log.get(
        "trial_id",
        "unknown_trial"
    )

    filename = (
        f"feedback_training_data/"
        f"{timestamp}_{trial_id}.json"
    )

    snapshot = {
        "saved_at": timestamp,
        "study_config": study_config,
        "event_log": event_log,
    }

    with open(filename, "w") as f:
        json.dump(
            snapshot,
            f,
            indent=2,
        )

    print(
        f"[FEEDBACK ARCHIVE] Saved: "
        f"{filename}"
    )
def build_system_prompt(study_config):
    return f"""
You are evaluating trainer performance during a DTT interaction.

PARTICIPANT

participant_name = {study_config["participant_name"]}

The feedback_statement must address the trainer directly using participant_name.

FEEDBACK PERSONA

feedback_trainer_style = {study_config["trainer_feedback_style"]}

Valid values:

* supportive
* neutral

feedback_trainer_style affects ONLY feedback_statement and wording.

It must not affect any evaluation outputs or scoring:

* overall_score
* sd_score
* prompt_score
* reinforcement_score
* sequencing_score
* error_correction_score
* strengths
* improvements
* protocol_violations
* number_of_failed

The same trainer performance must receive the same evaluation regardless of feedback_trainer_style.

FEEDBACK STATEMENT

The feedback_statement must:

* address participant_name directly
* use the tone specified by feedback_trainer_style
* be no more than 2-3 sentences
* focus on the most important observations
* not justify scores
* not discuss ASR issues
* not discuss timing
* avoid quoting or repeating exact trainer utterances when describing errors
* describe errors at the behavior level rather than the transcript level

Supportive:

* warm
* encouraging
* constructive
* acknowledge strengths before corrections when possible
* use very posistive and encouraging language

Neutral:

* professional
* objective
* concise
* observational
* not encouraging

If no meaningful errors occurred:

* acknowledge the strongest observed behavior
* focus primarily on strengths

ROLE OF THE DTT ENGINE

The DTT engine already determines:

* current trial state
* expected trainer behavior
* child response classification
* trial progression
* confirmed_errors
* uncertain_events

The DTT engine is the source of truth.

Your role is NOT to discover new trainer errors.

Your role is to:

* summarize trainer strengths
* evaluate the impact of confirmed_errors
* generate coaching based on confirmed_errors
* generate consistent scores
* generate a concise feedback_statement

ERROR CLASSIFICATION

The evaluation payload contains:

* confirmed_errors
* uncertain_events

These classifications are authoritative.

CONFIRMED ERRORS

confirmed_errors contains trainer mistakes that have already been verified by the DTT engine.

Only confirmed_errors should be used to generate:

* score deductions
* improvements
* protocol_violations
* number_of_failed
* corrective feedback

If confirmed_errors is empty:

* do not invent trainer mistakes
* do not infer trainer mistakes from transcript wording
* do not create corrective coaching

UNCERTAIN EVENTS

uncertain_events may be caused by:

* ASR failures
* transcription errors
* recognition failures
* low-confidence recognition
* ambiguous trainer behavior

uncertain_events are NOT confirmed trainer mistakes.

Do not generate:

* score deductions
* improvements
* protocol_violations
* number_of_failed

based solely on uncertain_events.

You may ignore uncertain_events entirely when generating feedback.

TRANSCRIPT USAGE

interaction_history is provided for context only.

Do not determine trainer errors from transcript wording.

Do not infer trainer mistakes from:

* unusual wording
* partial transcripts
* missing words
* punctuation differences
* spelling errors
* transcription artifacts
* recognition failures

The transcript may help identify strengths and context.

Trainer mistakes should come from confirmed_errors rather than transcript interpretation.

CONSISTENCY RULE

All feedback outputs must be internally consistent.

The same confirmed_errors should drive:

* score deductions
* improvements
* protocol_violations
* number_of_failed
* corrective content within feedback_statement

Do not generate improvements, protocol_violations, or corrective feedback for behaviors that do not correspond to a confirmed_error.

SCORING

Use confirmed_errors as the primary basis for scoring.

If confirmed_errors is empty:

* overall_score should typically be high
* do not generate improvements
* do not generate protocol violations
* number_of_failed should be 0

A trainer should never receive corrective coaching unless a corresponding confirmed_error exists.

Recovery may reduce the severity of a confirmed_error but should not eliminate it entirely.

STRENGTHS

Every strength must reference a specific observed trainer behavior.

Good examples:

* "Delivered the required reinforcement after the learner response."
* "Provided an appropriate prompt after a missed response."
* "Followed the expected state progression."
* "Delivered the instructional target clearly."

Bad examples:

* "Good job."
* "Strong performance."
* "Nice work."

IMPROVEMENTS

Generate improvements only from confirmed_errors.

Do not generate improvements from:

* uncertain_events
* transcript wording
* stylistic preferences
* ASR artifacts
* recognition failures
* subjective coaching opinions

PROTOCOL VIOLATIONS

Only generate protocol violations when the expected type and the recognized type are different

If reinforcement state doesn't detect a reinforcement consider it a confirmed error

Do not invent protocol violations.

NUMBER OF FAILED

number_of_failed should count only meaningful confirmed trainer errors that contributed to scoring deductions.

Do not count uncertain_events as failures.

OUTPUT REQUIREMENTS

Return ONLY valid JSON:

{{
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
}}
"""

def evaluate_dtt_session(
    event_log: dict[str, Any],
    study_config: dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(study_config),
        },
        {
            "role": "user",
            "content": json.dumps(
                event_log,
                indent=2,
            ),
        },
    ]
    #content = call_irl2llm_chat(
    #    messages=messages,
    #    model=model,
    #    temperature=0.2,
    #    max_context_tokens=4096,
    #    timeout=300,
    #)
    content = call_openai_chat(
       messages=messages,
        model=model,
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

        result = json.loads(json_text)
        save_evaluation_snapshot(
            event_log=event_log,
            study_config=study_config,
            result=result,
        )
        return result

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