from pathlib import Path
import json
import logic
from logic.feedback import evaluate_dtt_session

TEST_CASE_DIR = "feedback_training_data/asr_errors"

for file in Path(TEST_CASE_DIR).rglob("*.json"):

    print(f"\n===== {file.name} =====")

    with open(file) as f:
        test_case = json.load(f)

    event_log = test_case["event_log"]
    study_config = test_case["study_config"]
    result = evaluate_dtt_session(
        event_log=event_log,
        study_config=study_config,
    )

    print(json.dumps(result, indent=2))