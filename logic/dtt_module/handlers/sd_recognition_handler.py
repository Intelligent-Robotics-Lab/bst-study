from logic.dtt_module.models.enums import CurrentState


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

        current_sd = result.get(
            "matched_sd_id"
        )

        # ----------------------------------
        # Determine outcome type
        # ----------------------------------

        if current_sd is None:

            success = False

            result_type = (
                "uncertain"
            )

        elif (
            expected_sd is not None
            and current_sd != expected_sd
        ):

            success = False

            result_type = (
                "confirmed_error"
            )

        else:

            success = True

            result_type = "success"

        # ----------------------------------
        # Log transcript event
        # ----------------------------------

        self.log_transcript(
            feedback=feedback,
            trial_state=trial_state,
            transcript=transcript,
            recognized_as=current_sd,
            successful=success,
            result_type=result_type,
        )

        return {
            "current_sd": current_sd,
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