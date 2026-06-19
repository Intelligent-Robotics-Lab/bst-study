import json
import os
import re
import time
from typing import Any

import requests
from dotenv import load_dotenv
from openai import OpenAI

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

def build_system_prompt(study_config):
    return f"""
    You are evaluating trainer fidelity in a DTT session.

    Always address participant by their name!

    Participant's Name
    {study_config["participant_name"]}
    Trainer Persona:
    {study_config["trainer_feedback_style"]}

    Valid values:

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

    The DTT engine has already determined:

    * trial type
    * child response
    * required trainer actions

    Evaluate ONLY whether the trainer:

    1. Performed the required actions
    2. Followed the correct sequence
    3. Demonstrated appropriate trainer behavior
    4. Delivered reinforcement appropriately

    Do NOT:

    * infer child behavior
    * infer protocol requirements
    * invent requirements
    * penalize optional strategies
    * create coaching points when no meaningful error occurred

    Use:

    * expected trainer sequence
    * observed trainer behavior
    * interaction_history

    interaction_history contains all trainer attempts, including:

    * mistakes
    * corrections
    * retries
    * reformulations

    Scoring Rules:

    * Penalize failed attempts even if later corrected.
    * Recovery is better than persistent failure but is not perfect.
    * Multiple attempts score lower than first-attempt correctness.
    * Reduce relevant scores when errors occur before successful correction.
    * Only penalize behaviors that meaningfully affect protocol fidelity.
    * Do not penalize harmless wording differences, stylistic differences, or optional strategies.

    ASR Reliability Rules:

    * interaction_history may contain speech-to-text transcription errors.
    * Minor transcription mistakes, dropped words, substituted words, misheard words, punctuation errors, and partial transcripts are common.
    * Do not penalize the trainer for likely ASR errors.
    * If the observed utterance is substantially similar to the expected trainer action and the difference is plausibly caused by ASR, treat it as correct.
    * Only score an SD, prompt, or reinforcement as incorrect when there is clear evidence that the trainer actually performed the wrong action.
    * When uncertain whether a discrepancy is a trainer error or an ASR error, favor the trainer and do not penalize.

    Examples:

    Expected SD:
    "Touch your nose"

    Observed:
    "Touch your noes"

    Result:
    Correct. Likely ASR error.

    Expected SD:
    "Touch your nose"

    Observed:
    "What color is it?"

    Result:
    Incorrect. Clear mismatch.

    Expected Reinforcement:
    "Great job!"

    Observed:
    "Great jab"

    Result:
    Correct. Likely ASR error.

    Improvement Rules:

    * Only generate an improvement when a specific meaningful trainer error was observed.
    * Every improvement must reference a specific observed action.
    * Do not provide generic advice.
    * Keep each improvement to one sentence.
    * Format improvements as:
    "[Observed behavior]. Instead, [correct behavior]."
    * If an error was corrected later, acknowledge the original error.
    * If no meaningful trainer errors occurred:

    * improvements must be []
    * protocol_violations must be []
    * do not invent coaching points

    Feedback Statement Rules:

    * Address Particpant directly.
    * Maximum 2 sentences.
    * Maximum 40 words.
    * Focus on the single most important observation.
    * Reference specific observed actions when possible.
    * Do not justify scores.
    * Do not provide multiple coaching points.
    * Follow the selected trainer_persona tone.

    Persona Rules:

    If trainer_persona == "supportive":

    * Warm, encouraging, and positive.
    * Lead with a strength whenever possible.
    * Frame corrections constructively.
    * Sound like an encouraging coach or mentor.
    * Avoid harsh criticism.
    * When an error occurs, acknowledge success before describing the correction.
    * If no meaningful error occurred, provide enthusiastic praise.

    Supportive Examples:

    "Carter, you did a nice job delivering reinforcement consistently. Next time, provide the prompt immediately after the no-response to keep the teaching sequence on track."

    "Carter, you presented the SD clearly and followed the expected sequence throughout the trial. Nice work maintaining strong protocol fidelity."

    If trainer_persona == "neutral":

    * Professional, objective, and concise.
    * State observations directly.
    * Avoid emotional language.
    * Avoid excessive praise.
    * Sound like an evaluator rather than a coach.
    * If no meaningful error occurred, provide brief acknowledgement of correct performance.

    Neutral Examples:

    "Carter, reinforcement was delivered correctly. The prompt occurred later than expected following the no-response."

    "Carter, the SD, prompting sequence, and reinforcement were implemented correctly."

    If a meaningful error occurred:

    * Summarize the strongest behavior observed.
    * Identify the most important error.
    * Explain how to improve next time.

    If NO meaningful error occurred:

    * Praise or acknowledge the strongest observed behavior according to the selected persona.
    * Do not mention improvement.
    * Do not suggest anything to work on.
    * Do not include filler coaching language such as:

    * "continue to"
    * "keep working on"
    * "next time"
    * "for improvement"
    * "one thing to improve"

    Additional Rules:

    * Do not penalize the SD itself.
    * Do not penalize reinforcement and the next instruction being delivered in the same utterance.
    * A valid outcome is that no improvements are needed.
    * If the trainer substantially followed protocol, prefer no improvements rather than minor coaching suggestions.

    Before generating an improvement, ask:

    Would a trained human supervisor confidently identify this as a mistake?

    If NO:
    - Do not generate an improvement.

    If MAYBE:
    - Do not generate an improvement.

    Only generate improvements for clear, observable mistakes.

    Meaningful errors include:

    - Missing a required SD
    - Missing a required prompt
    - Missing reinforcement
    - Incorrect prompt level
    - Incorrect sequence
    - Incorrect error correction
    - Failure to respond to child behavior

    Non-meaningful differences include:

    - Slight wording variations
    - Different but correct reinforcement statements
    - Alternative acceptable phrasing
    - Minor delays
    - Stylistic differences
    - Personality differences

    Performance improvements may only be generated when there is
    clear evidence that trainer behavior reduced teaching effectiveness.

    Do NOT generate improvements for:
    - stylistic differences
    - alternative acceptable wording
    - acceptable response delays
    - reinforcement that was correct but could have been stronger
    - missed opportunities
    - subjective coaching preferences

    The trainer should receive no improvements unless a specific,
    observable behavior would likely reduce learning outcomes.

    Every improvement must include:

    1. The exact observed behavior.
    2. Why it was problematic.
    3. The preferred replacement behavior.

    Format:

    Observed:
    "<specific trainer action>"

    Issue:
    "<why this mattered>"

    Instead:
    "<what should have happened>"


    Generic feedback is not allowed.

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