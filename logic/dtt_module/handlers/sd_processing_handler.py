from logic.dtt_module.models.enums import CurrentState, TrialState


class SDProcessingHandler:

    def __init__(
        self,
        interaction_manager,
        perception_agent,
        log_transcript_callback,
    ):
        self.interaction = interaction_manager
        self.perception_agent = perception_agent
        self.log_transcript = log_transcript_callback

    async def handle_completed_sd(
        self,
        *,
        ctx,
        expr,
    ):

        text = (
            f"You have already completed "
            f"{ctx.current_sd}. "
            f"Please move onto a different SD."
        )

        await self.interaction.speak_text(
            expr=expr,
            text=text,
        )

        self.perception_agent.state.latest_transcript = None

        ctx.current_sd = None
        ctx.trial_sd = None

        ctx.state = CurrentState.USER
        ctx.trial_state = TrialState.SD

    async def process_sd_result(
        self,
        *,
        ctx,
        transcript,
        feedback,
        expr,
        trial_data,
    ):

        print(f"[SD DETECTED] {ctx.current_sd}")

        feedback.reset()

        self.log_transcript(
            feedback=feedback,
            trial_state=TrialState.SD,
            transcript=transcript,
            recognized_as=ctx.current_sd,
            successful=(ctx.current_sd is not None),
        )

        if ctx.current_sd is None:

            await self.interaction.set_led(
                expr=expr,
                color="#FF0000",
                action="on",
                flash=True,
                embodiment="kid",
            )

            ctx.state = CurrentState.USER
            ctx.trial_state = TrialState.SD

            return

        feedback.trial_id = ctx.current_sd

        feedback.expected_sd = (
            trial_data[ctx.current_sd]["sd"]
        )

        feedback.correctness = (
            trial_data[ctx.current_sd]["correctness"]
        )

        ctx.state = CurrentState.KID
        ctx.trial_state = TrialState.KID_BEHAVIOR_1