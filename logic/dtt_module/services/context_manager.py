class ContextManager:

    def refresh(
        self,
        *,
        ctx,
        perception,
    ):

        ctx.transcript = (
            perception.state.latest_transcript
        )

        ctx.emotion = (
            perception.state.latest_emotion
        )

        print(
            f"\n[STATE] {ctx.state} | {ctx.trial_state}"
        )

        print(
            f"[TRACK] trial_sd={ctx.trial_sd} "
            f"current_sd={ctx.current_sd}"
        )