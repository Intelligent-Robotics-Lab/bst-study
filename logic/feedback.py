import requests
import json
import re
import time


OLLAMA_URL = "http://localhost:11434/api/chat"


SYSTEM_PROMPT = """
You are evaluating trainer fidelity in a DTT session.

You will receive:
- trial_type
- protocol_expectations
- precomputed_analysis
- trainer_behavior
- child_behavior

IMPORTANT:
Only evaluate behaviors REQUIRED by protocol_expectations.

If:
"requires_prompting": false
then:
- do NOT penalize missing prompting
- do NOT penalize missing error correction

If:
"requires_error_correction": false
then:
- do NOT penalize missing retry SD
- do NOT penalize missing HP sequence

If:
"requires_reinforcement": true
then reinforcement MUST occur.

IMPORTANT:
- Reinforcement may repeat the SD.
- Repeating the SD during reinforcement is NOT an error.
- Evaluate ONLY the trainer.
- Do NOT hallucinate missing actions.
- Use precomputed_analysis heavily.
- Trust deterministic scoring over assumptions.

Scoring:
- 100 = perfect fidelity
- 70-90 = minor procedural issues
- below 70 = meaningful protocol violations

Output ONLY valid raw JSON.

No markdown.
No explanations.
No code fences.

Required JSON schema:

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
  "feedback_statement": str
}
"""


class FeedbackHolder:

    def __init__(self):
        self.reset()

    def reset(self):

        self.trial_id = None
        self.expected_sd = None
        self.correctness = None

        self.trainer_events = []
        self.child_events = []

    # =====================================================
    # EVENT RECORDING
    # =====================================================

    def add_trainer_event(self, event_type, text, t=None):

        self.trainer_events.append({
            "type": event_type,
            "text": text,
            "time": t if t else time.time()
        })

    def add_child_event(self, text, correct=None, t=None):

        self.child_events.append({
            "text": text,
            "correct": correct,
            "time": t if t else time.time()
        })

    # =====================================================
    # PAYLOAD GENERATION
    # =====================================================

    def build_evaluation_payload(self):

        # -------------------------------------------------
        # DETERMINE TRIAL TYPE
        # -------------------------------------------------

        is_correct_trial = self.correctness == "Correct"

        if is_correct_trial:

            trial_type = "correct_response_trial"

            expected_sequence = [
                "sd",
                "child_correct_response",
                "reinforcement"
            ]

        else:

            trial_type = "error_correction_trial"

            expected_sequence = [
                "sd",
                "child_incorrect_or_no_response",
                "prompt",
                "prompted_response",
                "high_probability_sd",
                "retry_sd",
                "reinforcement"
            ]

        # -------------------------------------------------
        # DETECT TRAINER EVENTS
        # -------------------------------------------------

        prompt_detected = any(
            e["type"] == "prompt"
            for e in self.trainer_events
        )

        reinforcement_detected = any(
            e["type"] == "reinforcement"
            for e in self.trainer_events
        )

        hp_detected = any(
            e["type"] == "high_probability_sd"
            for e in self.trainer_events
        )

        retry_detected = any(
            e["type"] == "retry_sd"
            for e in self.trainer_events
        )

        sd_detected = any(
            e["type"] == "sd"
            for e in self.trainer_events
        )

        # -------------------------------------------------
        # DETERMINE REQUIREMENTS
        # -------------------------------------------------

        requires_prompting = not is_correct_trial

        requires_error_correction = not is_correct_trial

        requires_reinforcement = True

        # -------------------------------------------------
        # DETERMINISTIC PROCEDURAL SCORING
        # -------------------------------------------------

        sd_fidelity_preliminary = (
            100 if sd_detected else 0
        )

        prompt_fidelity_preliminary = 100

        if requires_prompting:

            if not prompt_detected:
                prompt_fidelity_preliminary = 0

        else:

            if prompt_detected:
                prompt_fidelity_preliminary = 50

        reinforcement_fidelity_preliminary = (
            100
            if reinforcement_detected == requires_reinforcement
            else 0
        )

        error_correction_fidelity_preliminary = 100

        if requires_error_correction:

            if not hp_detected:
                error_correction_fidelity_preliminary -= 50

            if not retry_detected:
                error_correction_fidelity_preliminary -= 50

        # -------------------------------------------------
        # SEQUENCE ANALYSIS
        # -------------------------------------------------

        actual_sequence = []

        for e in self.trainer_events:

            actual_sequence.append(e["type"])

        sequence_match_count = 0

        for expected_step in expected_sequence:

            if expected_step in actual_sequence:
                sequence_match_count += 1

        sequencing_score_preliminary = int(
            (sequence_match_count / len(expected_sequence)) * 100
        )

        # -------------------------------------------------
        # OVERALL PRELIMINARY SCORE
        # -------------------------------------------------

        preliminary_scores = [
            sd_fidelity_preliminary,
            prompt_fidelity_preliminary,
            reinforcement_fidelity_preliminary,
            sequencing_score_preliminary,
            error_correction_fidelity_preliminary
        ]

        overall_preliminary_score = int(
            sum(preliminary_scores) / len(preliminary_scores)
        )

        # -------------------------------------------------
        # FINAL PAYLOAD
        # -------------------------------------------------

        return {

            "trial_id": self.trial_id,

            "trial_type": trial_type,

            "protocol_expectations": {

                "expected_sd": self.expected_sd,

                "child_response_type": self.correctness,

                "requires_prompting": requires_prompting,

                "requires_error_correction": (
                    requires_error_correction
                ),

                "requires_reinforcement": (
                    requires_reinforcement
                ),

                "expected_sequence": expected_sequence
            },

            "precomputed_analysis": {

                "sd_detected": sd_detected,

                "prompt_detected": prompt_detected,

                "reinforcement_detected": (
                    reinforcement_detected
                ),

                "high_probability_sd_detected": (
                    hp_detected
                ),

                "retry_sd_detected": retry_detected,

                "actual_sequence": actual_sequence,

                "sd_fidelity_preliminary": (
                    sd_fidelity_preliminary
                ),

                "prompt_fidelity_preliminary": (
                    prompt_fidelity_preliminary
                ),

                "reinforcement_fidelity_preliminary": (
                    reinforcement_fidelity_preliminary
                ),

                "error_correction_fidelity_preliminary": (
                    error_correction_fidelity_preliminary
                ),

                "sequencing_score_preliminary": (
                    sequencing_score_preliminary
                ),

                "overall_preliminary_score": (
                    overall_preliminary_score
                )
            },

            "trainer_behavior": self.trainer_events,

            "child_behavior": self.child_events
        }


# =====================================================
# JSON EXTRACTION
# =====================================================

def extract_json(text):

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        return match.group(0)

    return None


# =====================================================
# MAIN EVALUATOR
# =====================================================

def evaluate_dtt_session(
    event_log,
    model="llama3.1:8b"
):

    payload = {

        "model": model,

        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": json.dumps(
                    event_log,
                    indent=2
                )
            }
        ],

        "stream": False,

        # VERY IMPORTANT
        # Forces structured JSON output
        "format": {
            "type": "object",
            "properties": {

                "overall_score": {
                    "type": "integer"
                },

                "sd_score": {
                    "type": "integer"
                },

                "prompt_score": {
                    "type": "integer"
                },

                "reinforcement_score": {
                    "type": "integer"
                },

                "sequencing_score": {
                    "type": "integer"
                },

                "error_correction_score": {
                    "type": "integer"
                },

                "strengths": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "improvements": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "protocol_violations": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "feedback_statement": {
                    "type": "string"
                }
            },

            "required": [
                "overall_score",
                "sd_score",
                "prompt_score",
                "reinforcement_score",
                "sequencing_score",
                "error_correction_score",
                "strengths",
                "improvements",
                "protocol_violations",
                "feedback_statement"
            ]
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload
    )

    if response.status_code != 200:

        raise Exception(
            f"Ollama Error: {response.text}"
        )

    result = response.json()

    content = result["message"]["content"]

    print("\n===== RAW LLM OUTPUT =====")
    print(content)

    json_text = extract_json(content)

    if json_text is None:

        print("\nFAILED TO EXTRACT JSON")

        return {

            "overall_score": 0,
            "sd_score": 0,
            "prompt_score": 0,
            "reinforcement_score": 0,
            "sequencing_score": 0,
            "error_correction_score": 0,

            "strengths": [],

            "improvements": [
                "Failed to extract JSON from model output"
            ],

            "protocol_violations": [
                "Invalid model output"
            ],

            "feedback_statement": (
                "Unable to generate feedback."
            )
        }

    try:

        parsed = json.loads(json_text)

        return parsed

    except Exception as e:

        print("\nJSON PARSE ERROR")
        print(e)

        return {

            "overall_score": 0,
            "sd_score": 0,
            "prompt_score": 0,
            "reinforcement_score": 0,
            "sequencing_score": 0,
            "error_correction_score": 0,

            "strengths": [],

            "improvements": [
                "JSON parsing failed"
            ],

            "protocol_violations": [
                str(e)
            ],

            "feedback_statement": (
                "Unable to generate feedback."
            )
        }