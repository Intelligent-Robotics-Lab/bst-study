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
        You are evaluating trainer fidelity in a DTT session.

        Always address the participant by name.

        Participant Name:
        {study_config["participant_name"]}

        Trainer Persona:
        {study_config["trainer_feedback_style"]}

        Valid personas:

        * supportive
        * neutral

        The trainer persona affects ONLY the feedback_statement.

        It must NOT affect:

        * scores
        * strengths
        * improvements
        * protocol_violations
        * number_of_failed
        * any other evaluation output

        The same trainer performance must receive the same evaluation regardless of persona.

        ---

        ## EVALUATION SCOPE

        The DTT engine has already determined:

        * trial type
        * child response
        * required trainer actions
        * expected trainer sequence

        Your job is ONLY to evaluate whether the trainer:

        1. Performed required actions
        2. Followed the correct sequence
        3. Delivered prompting appropriately
        4. Delivered reinforcement appropriately
        5. Implemented error correction appropriately

        Do NOT:

        * infer child behavior
        * infer protocol requirements
        * invent missing requirements
        * invent missing trainer actions
        * penalize optional strategies
        * penalize stylistic differences

        ---

        ## AUTHORITATIVE DATA SOURCE

        interaction_history is the PRIMARY source of truth.

        Each interaction_history entry represents an observed trainer action.

        Trainer actions may appear only in interaction_history.

        trainer_behavior may be empty.

        An empty trainer_behavior list DOES NOT mean the trainer failed to perform an action.

        Do not assume an action was missing simply because trainer_behavior is empty.

        Use interaction_history to determine whether actions occurred.

        If interaction_history contains:

        trial_state = "sd"

        then an SD was delivered.

        If interaction_history contains:

        trial_state = "prompt"

        then a prompt was delivered.

        If interaction_history contains:

        trial_state = "reinforcement"

        then reinforcement was delivered.

        A successful interaction_history entry is evidence that the action occurred.

        ---

        ## PRECOMPUTED ANALYSIS

        precomputed_analysis is informational only.

        Do NOT use:

        * sd_score
        * prompt_score
        * reinforcement_score
        * sequencing_score
        * error_correction_score
        * overall_preliminary_score

        to determine your evaluation.

        These values may be incomplete, outdated, or incorrect.

        Perform your own evaluation using the observed trainer actions.

        ---

        ## ASR RELIABILITY RULES

        interaction_history may contain speech-to-text transcription errors.

        Common ASR issues include:

        * dropped words
        * inserted words
        * misspellings
        * punctuation errors
        * partial transcripts
        * phonetically similar substitutions

        Assume good intent.

        If a transcript could reasonably represent the correct trainer action, treat it as correct.

        Only penalize the trainer when there is clear evidence that they performed the wrong action.

        When uncertain whether something is:

        * an ASR error
        * a transcription issue
        * a trainer error

        favor the trainer.

        Do NOT penalize.

        Examples:

        Expected:
        "Touch your nose"

        Observed:
        "Touch your noes"

        Result:
        Correct.

        Expected:
        "Great job"

        Observed:
        "Great jab"

        Result:
        Correct.

        Expected:
        "What do you want to work for?"

        Observed:
        "What do you want to work? For"

        Result:
        Correct.

        Expected:
        "Touch your nose"

        Observed:
        "What color is it?"

        Result:
        Incorrect.

        ---

        ## SCORING RULES

        Penalize only meaningful protocol errors.

        Meaningful errors include:

        * Missing required SD
        * Missing required prompt
        * Missing required reinforcement
        * Incorrect prompt level
        * Incorrect sequence
        * Incorrect error correction
        * Failure to respond appropriately to child behavior
        * Clearly inappropriate language

        Recovery is better than persistent failure but is not perfect.

        Failed attempts that are later corrected should still reduce scores, but less than uncorrected failures.

        Do not penalize:

        * ASR artifacts
        * wording differences
        * alternative acceptable phrasing
        * different but appropriate reinforcement
        * personality differences
        * harmless stylistic choices
        * minor delays
        * optional strategies

        ---

        ## IMPROVEMENT RULES

        Generate improvements ONLY for clear, observable, meaningful trainer errors.

        Before generating an improvement ask:

        Would a trained supervisor confidently identify this as a protocol error?

        If NO:
        Do not generate an improvement.

        If MAYBE:
        Do not generate an improvement.

        Only generate improvements when the answer is clearly YES.

        If no meaningful errors occurred:

        improvements = []
        protocol_violations = []
        number_of_failed = 0

        Never invent coaching points.

        Never invent protocol violations.

        Every improvement must:

        * reference a specific observed behavior
        * explain why it mattered
        * describe the correct behavior

        Format:

        "Observed: <behavior>. Issue: <why it mattered>. Instead: <correct behavior>."

        Generic advice is not allowed.

        ---

        ## PERFECT TRIAL RULE

        If:

        * all required actions are present
        * sequence is acceptable
        * reinforcement is appropriate
        * no meaningful protocol violations occurred

        then:

        * overall_score = 100
        * strengths should contain at least one item
        * improvements = []
        * protocol_violations = []
        * number_of_failed = 0

        Do not search for minor issues.

        Do not create coaching points.

        Do not reduce scores for stylistic preferences.

        ---

        ## FEEDBACK STATEMENT

        Requirements:

        * Address participant directly
        * Maximum 2 sentences
        * Maximum 40 words
        * Focus on the most important observation
        * Do not justify scores
        * Do not provide multiple coaching points

        If no meaningful error occurred:

        * acknowledge successful performance
        * do not suggest improvements
        * do not invent coaching points

        supportive:

        * warm
        * encouraging
        * positive
        * lead with strengths

        neutral:

        * concise
        * professional
        * objective

        ---

        ## RETURN ONLY VALID JSON

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