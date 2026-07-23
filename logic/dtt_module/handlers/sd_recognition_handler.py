from logic.dtt_module.models.enums import (
    CurrentState,
)
from logic.dtt_module.models.enums import TrialState

class SDRecognitionHandler:

    def __init__(
        self,
        log_transcript_callback,
    ):
        self.log_transcript = (
            log_transcript_callback
        )

    async def handle_sd_recognition(
        self,
        *,
        transcript,
        emotion,
        recognizer,
        feedback,
        trial_state,
        expected_sd,
        next_trial_state,
        state,
        last_processed,
    ):

        # Ignore empty or duplicate transcripts
        if (
            not transcript
            or transcript == last_processed
        ):
            return None

        observed = {
            "verbal_text": transcript,
            "emotion": emotion,
        }

        result = recognizer.recognize(
            observed_input=observed
        )

        # Exact thing matched in master_data.json
        recognized_id = result.get(
            "matched_sd_id"
        )

        # sd, hp_sd, reinforcement, or None
        recognized_type = result.get(
            "matched_type"
        )

        # current_sd should ONLY contain
        # actual trial SDs
        if recognized_type == "sd":
            current_sd = recognized_id
        else:
            current_sd = None

        print(
            f"Recognized: "
            f"{recognized_id} "
            f"({recognized_type})"
        )

        # ----------------------------
        # Determine outcome type
        # ----------------------------

        if recognized_id is None:
            success = False
            result_type = "uncertain"

        elif (
            trial_state == TrialState.REINFORCEMENT
        ):
            # Do not confirm recognition errors during reinforcement.
            # Reinforcement is not evaluated against expected_sd.
            success = False
            result_type = "uncertain"

        elif (
            expected_sd is not None
            and recognized_id != expected_sd
        ):
            success = False
            result_type = "confirmed_error"

        else:
            success = True
            result_type = "success"

        # ----------------------------
        # Log transcript event
        # ----------------------------

        self.log_transcript(
            feedback=feedback,
            trial_state=trial_state,
            transcript=transcript,
            recognized_as=recognized_id,
            recognized_type=recognized_type,
            successful=success,
            result_type=result_type,
        )

        return {
            # Only actual SDs
            "current_sd": current_sd,

            # For feedback
            "recognized_id": recognized_id,
            "recognized_type": recognized_type,

            "success": success,
            "result_type": result_type,

            "next_state": (
                CurrentState.KID
                if success
                else state
            ),

            "next_trial_state": (
                next_trial_state
                if success
                else trial_state
            ),

            "last_processed": transcript,
        }