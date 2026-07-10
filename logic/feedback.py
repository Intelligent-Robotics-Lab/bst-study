import json
import os
import re
import time
from typing import Any

import requests
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from datetime import datetime, timezone
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
            # Wall clock for this attempt. Without it every step would reach the
            # data platform stamped with the end-of-trial post time, and all
            # intra-trial timing would be lost.
            "time": time.time(),
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

    # =====================================================
    # DATA PLATFORM: within-trial interaction flow
    # =====================================================

    def to_trial_steps(self) -> list[dict[str, Any]]:
        """interaction_history -> the data platform's `steps` payload.

        Only the trainer's attempts are recorded: the child's behaviour is
        scripted, so it carries no information. A trial_state may repeat (e.g.
        two hp_sd attempts, the first unrecognised) -- step_index orders them.

        Sends nothing from study_config: research data holds participant IDs,
        never names. Sends no precomputed_analysis: the operator must score
        fidelity blind to any machine score.
        """
        steps: list[dict[str, Any]] = []
        for i, event in enumerate(self.interaction_history, start=1):
            step: dict[str, Any] = {
                "step_index": i,
                # "retry sd" -> "retry_sd"; the rest already match
                "step_label": str(event["trial_state"]).replace(" ", "_"),
                "actor": "user",  # the human trainer
                "outcome": "recognized" if event.get("successful") else "not_recognized",
                "detail": {
                    "text": event.get("text"),
                    "recognized_as": event.get("recognized_as"),
                    "corrected_later": event.get("corrected_later", False),
                },
            }
            when = event.get("time")
            if when is not None:
                step["timestamp_utc"] = datetime.fromtimestamp(
                    when, timezone.utc
                ).isoformat()
            steps.append(step)
        return steps

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

It must not affect any evaluation outputs or scoring: overall_score, sd_score, prompt_score, reinforcement_score, sequencing_score, error_correction_score, strengths, improvements, protocol_violations, number_of_failed.

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
* reference specific moments only when necessary for clarity

Supportive:

* warm
* encouraging and using encouraging language at all times
* constructive
* acknowledge strengths before corrections when possible

Neutral:

* professional
* objective
* concise
* state observations directly
* not encouragement

If no meaningful errors occurred:

* acknowledge the strongest observed behavior

CONSISTENCY RULE

All feedback outputs must be internally consistent.

The same meaningful trainer errors should drive:

* score deductions
* number_of_failed
* improvements
* protocol_violations
* feedback_statement

Do not generate improvements, protocol_violations, or feedback comments for behaviors that were not considered meaningful errors during scoring.

The DTT engine already determines:

* current trial state
* expected trainer behavior
* child response classification
* trial progression

Your job is to evaluate how well the trainer responded to the active trial state.

PRIMARY EVALUATION CRITERIA

Evaluate two things:

1. Content Accuracy

   * Did the trainer deliver the correct instructional content?
   * Did the trainer stay on the intended instructional target?
   * Was reinforcement appropriate?
   * Was language professional?

2. State Fidelity

   * Did the trainer deliver the correct behavior for the current trial state?
   * Did the trainer respond to the active state rather than a different state?

The trainer should not be penalized for minor wording differences.

WORDING RULE

Semantically equivalent wording should be treated as correct.

Example:

Expected:
"Touch your nose."

Observed:
"Can you touch your nose?"

Result:
Correct.

Example:

Expected:
"Touch your nose."

Observed:
"Show me your nose."

Result:
Correct.

Example:

Expected:
"Touch your nose."

Observed:
"What color is it?"

Result:
Incorrect. Different instructional targets.

REINFORCEMENT RULE

Reinforcement should be positive and clearly function as reinforcement.

Reasonable variation in reinforcement wording is acceptable. Do not penalize reinforcement for lacking enthusiasm if it still acknowledges performance and functions as reinforcement.

Examples of valid reinforcement:

* "Great job!"
* "Nice work!"
* "Awesome!"
* "You got it!"
* "We can do that!"

Examples of invalid reinforcement:

* delivering a new instructional SD
* delivering a prompt
* unrelated statements
* neutral statements that don't acknowledge the response

Only generate a reinforcement error when there is clear evidence that reinforcement was missing, inappropriate, or replaced with a different instructional behavior.

If uncertain whether an utterance functioned as reinforcement, favor the trainer and do not apply a penalty as it was likely an ASR error.

ASR RELIABILITY

interaction_history may contain transcription errors.

Do not penalize:

* spelling errors
* missing words
* transcription mistakes
* punctuation differences
* partial transcripts

Only score an SD, prompt, reinforcement, or high-probability SD as incorrect when there is clear evidence that the trainer performed the wrong action.

When uncertain whether a discrepancy is caused by ASR or trainer behavior, favor the trainer and do not apply a penalty.

REPETITION RULE

Repeated identical utterances are common due to:

* ASR artifacts
* recognition retries
* logging artifacts
* system retries

Do not treat repeated identical or semantically similar utterances as errors.

Example:

"Touch your nose."
"Touch your nose."

Result:
No penalty.

STATE FIDELITY EXAMPLES

Expected State:
PROMPT

Observed:
Reinforcement

Result:
State fidelity error.

Expected State:
HIGH_PROBABILITY_SD

Observed:
Target instructional SD

Result:
State fidelity error.

Expected State:
REINFORCEMENT

Observed:
New instructional target

Result:
State fidelity error.

HIGH PROBABILITY SD RULE

High-probability SD states may have many valid responses.

The evaluator may not have visibility into every acceptable high-probability SD.

When evaluating HIGH_PROBABILITY_SD states:

* prioritize state fidelity over SD selection
* do not assume a specific high-probability SD is required
* allow reasonable variation in high-probability SD choice
* do not compare the observed SD against an expected example SD
* any reasonable high-probability SD should be treated as correct for the state

Only generate an error when there is clear evidence that the trainer delivered a behavior from a different trial state.

Examples of behaviors from a different state:
* reinforcement
* prompting
* error correction
* target instructional SD delivery when a high-probability SD was expected

If uncertain whether a high-probability SD was appropriate, favor the trainer and do not apply a penalty.

TRANSCRIPT-ONLY EVALUATION

Evaluate only behaviors observable in the transcript and interaction_history.

Do not infer:

* trainer intentions
* timing errors
* delays
* missing actions that are not observable
* unobserved protocol violations

Only generate errors when there is clear transcript evidence of a meaningful trainer mistake.

RECOVERY

The trainer may make multiple attempts before the system accepts a response.

A corrected error should receive a smaller penalty than an uncorrected error.

Recovery demonstrates partial success.

If the trainer repeats the same or a semantically similar utterance multiple times in a row, treat this as a potential system retry rather than multiple trainer errors.

Do not heavily penalize repeated attempts unless the content itself was incorrect for the active state.

ERROR SEVERITY

Minor Errors:

* likely ASR issues
* semantically similar wording
* recoverable recognition failures

Moderate Errors:

* incorrect content for the active state
* incorrect instructional target with later recovery
* delivering the wrong behavior for the current state

Major Errors:

* repeated state fidelity errors
* inappropriate language
* persistent failure to respond to the active state

Recovery should reduce the severity of an error but should not eliminate it entirely.

SCORING

Scores should reflect:

* content accuracy
* state fidelity
* severity of observed errors
* successful recovery

Minor errors should result in small deductions.

Recovered errors should receive smaller deductions than persistent errors.

Do not heavily penalize:

* ASR issues
* duplicate utterances
* semantically equivalent wording
* valid high-probability SD variations

FEEDBACK GENERATION

All feedback outputs must be based on the same underlying evaluation.

STRENGTHS

Every strength must reference a specific observed behavior.

Good:

* "Delivered the required reinforcement after the correct response."
* "Followed the expected state progression."

Bad:

* "Good job."
* "Strong performance."

IMPROVEMENTS

Generate improvements only for clear, observable fidelity errors.

Do not generate improvements for:

* stylistic differences
* semantically equivalent wording
* repeated utterances
* ASR issues
* subjective coaching preferences

PROTOCOL VIOLATIONS

Only generate a protocol violation when there is clear evidence in the transcript.

Do not infer missing behaviors.

Do not invent protocol violations.

NUMBER OF FAILED

number_of_failed should count only meaningful trainer errors that contribute to scoring deductions.

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