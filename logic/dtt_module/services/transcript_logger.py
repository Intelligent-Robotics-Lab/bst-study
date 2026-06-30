# logic/dtt/services/transcript_logger.py

class TranscriptLogger:

    def log(
        self,
        *,
        feedback,
        trial_state,
        transcript,
        recognized_as=None,
        successful=False,
        result_type="success",
    ):
        feedback.add_transcript_event(
            trial_state=trial_state.value,
            text=transcript,
            recognized_as=recognized_as,
            successful=successful,
            result_type=result_type,
        )