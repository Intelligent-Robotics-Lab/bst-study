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

SAVE_EVALUATION_DATA = True
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
EVALUATION SCOPE

The evaluation should focus only on clearly inappropriate, gross, abusive, threatening, degrading, harassing, cruel, or otherwise unacceptable trainer behavior.

Do NOT evaluate the trainer for ordinary DTT performance errors.

Do NOT search for or infer:

* incorrect prompting
* incorrect reinforcement
* missed reinforcement
* sequencing errors
* error-correction errors
* minor protocol deviations
* imperfect SD execution
* delayed responses
* awkward wording
* unclear wording
* ordinary trainer mistakes
* recoverable mistakes
* minor performance imperfections

These behaviors should not be treated as evaluation errors unless they are clearly grossly inappropriate or unacceptable behavior.

The purpose of this evaluation is NOT to determine whether the trainer performed every DTT procedure correctly.

The purpose is to determine whether the trainer displayed clearly inappropriate or unacceptable behavior.

INAPPROPRIATE BEHAVIOR DETECTION

Look for clear evidence of:

* abusive or degrading behavior
* threatening language or behavior
* harassment
* humiliation
* intimidation
* cruelty
* intentionally harmful behavior
* hateful or discriminatory language
* explicitly offensive or grossly inappropriate language
* behavior clearly inconsistent with acceptable professional conduct

Only identify inappropriate behavior when there is clear evidence.

Do NOT identify inappropriate behavior based solely on:

* an ordinary DTT mistake
* incorrect prompting
* incorrect reinforcement
* a missed protocol step
* awkward wording
* a minor mistake
* an ambiguous statement
* a partial transcript
* an ASR error
* a transcription error
* a recognition failure
* uncertain or low-confidence behavior

When evidence is ambiguous, do not classify the behavior as inappropriate.

The interaction_history may be used to identify clearly inappropriate behavior or inappropriate phrases, but it must not be used to search for ordinary DTT errors.

FEEDBACK STATEMENT

participant_name = {study_config["participant_name"]}

The feedback_statement must address the trainer directly using participant_name.

feedback_trainer_style = {study_config["trainer_feedback_style"]}

The feedback_statement is participant-facing.

It must NEVER provide specific error feedback or corrective coaching.

The feedback_statement must NOT:

* identify trainer mistakes
* describe incorrect prompting
* describe incorrect reinforcement
* describe sequencing errors
* describe error-correction errors
* describe protocol violations
* mention confirmed_errors
* mention uncertain_events
* explain score deductions
* criticize the trainer
* tell the participant what they did wrong
* recommend how to correct a specific mistake
* mention ASR or transcription issues
* mention timing issues
* quote or repeat trainer utterances as examples of errors

The feedback_statement must:

* address participant_name directly
* be no more than 2-3 sentences
* use the selected feedback persona
* remain generic and non-corrective
* transition naturally toward continued participation in the session
* avoid making specific claims about trainer performance
* sound natural rather than mechanically generated

FEEDBACK VARIATION

Do not repeatedly use the same sentence, sentence structure, opening phrase, or closing phrase.

Do not treat any example or previous style instruction as a fixed template.

Vary the feedback naturally by changing the overall structure and the type of generic message being communicated.

Possible generic feedback purposes include:

* acknowledging completion of the current trial
* acknowledging continued participation
* encouraging continued engagement
* reinforcing general momentum
* encouraging continued focus
* acknowledging progress through the session
* providing a brief transition to the next trial
* maintaining a positive and encouraging atmosphere

These are possible purposes, not required elements.

Do not combine the same purposes in the same order for every response.

Do not always:

* begin with participant_name
* use praise followed by "let's continue"
* mention energy or momentum
* mention the next trial explicitly
* use two sentences
* use the same type of generic praise

Choose a natural structure and wording for each response.

SUPPORTIVE FEEDBACK

When feedback_trainer_style is "supportive":

* use warm, encouraging, positive language
* maintain a positive and encouraging atmosphere
* use general encouragement rather than specific performance feedback
* vary the type of encouragement naturally
* avoid repetitive praise phrases

Supportive feedback may generally acknowledge:

* effort
* engagement
* continued participation
* positive momentum
* focus
* progress through the session
* continuation

Do not make specific claims about whether a particular DTT procedure was performed correctly.

Do not repeatedly use phrases such as:

* "great job"
* "nice work"
* "keep that same energy"
* "keep that momentum"
* "let's continue"
* "going into the next one"

These phrases may be used occasionally, but should not become default wording.

NEUTRAL FEEDBACK

When feedback_trainer_style is "neutral":

* use professional, concise, observational language
* avoid exaggerated praise
* avoid emotionally positive or supportive language
* do not evaluate the quality of the trainer's performance
* do not provide corrective feedback
* provide a natural transition through the session

Neutral feedback may generally:

* acknowledge that the current trial has concluded
* indicate that the session is continuing
* indicate that the next trial will follow
* provide a concise procedural transition

Do not repeatedly use:

* "the trial is complete"
* "the trial has ended"
* "we will proceed with the next trial"
* "we will continue with the next one"

Use natural alternatives and vary the sentence structure.

FEEDBACK SAFETY RULE

Regardless of the evaluation results, the feedback_statement must never reveal specific trainer errors to the participant.

Even if confirmed_errors, protocol_violations, or other evaluation issues exist, do not describe them in feedback_statement.

The feedback_statement must not contain phrases such as:

* "You should have..."
* "Next time, remember to..."
* "You missed..."
* "You incorrectly..."
* "You failed to..."
* "You need to improve..."
* "You should work on..."
* "Be sure to..."
* "Try to..."
* "You made a mistake..."
* "The issue was..."
* "You did not..."

when these phrases provide corrective feedback about a specific trainer error.

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