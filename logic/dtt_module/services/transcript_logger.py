# logic/dtt/services/transcript_logger.py

class TranscriptLogger:

    def log(
        self,
        feedback,
        trial_state,
        transcript,
        recognized_as,
        recognized_type=None,
        successful=False,
        result_type=None,
    ):
        feedback.add_transcript_event(
            trial_state=trial_state.value,
            text=transcript,
            recognized_as=recognized_type,
            successful=successful,
            result_type=result_type,
        )