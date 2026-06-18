import asyncio

from logic.dtt_module.models.enums import (
    TrialState,
)


class HPSDHandler:

    def __init__(
        self,
        interaction_manager,
        perception_agent,
        sd_recognition_handler,
        reset_inactivity_timer_callback,
    ):
        self.interaction = interaction_manager
        self.perception_agent = perception_agent
        self.sd_recognition_handler = (
            sd_recognition_handler
        )
        self.reset_inactivity_timer = (
            reset_inactivity_timer_callback
        )

    async def handle(
        self,
        *,
        ctx,
        hp_recognizer,
        feedback,
        expr,
    ):

        await self.interaction.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        result = (
            await self.sd_recognition_handler.handle_sd_recognition(
                transcript=(
                    self.perception_agent.state.latest_transcript
                ),
                emotion=(
                    self.perception_agent.state.latest_emotion
                ),
                recognizer=hp_recognizer,
                feedback=feedback,
                trial_state=ctx.trial_state,
                expected_sd=None,
                next_trial_state=(
                    TrialState.KID_BEHAVIOR_HP
                ),
                state=ctx.state,
                last_processed=ctx.last_processed,
            )
        )

        if result:

            ctx.last_processed = (
                result["last_processed"]
            )

            ctx.current_sd = (
                result["current_sd"]
            )

            if result["success"]:

                self.reset_inactivity_timer(ctx)

                ctx.state = (
                    result["next_state"]
                )

                ctx.trial_state = (
                    result["next_trial_state"]
                )

            else:

                await self.interaction.set_led(
                    expr=expr,
                    color="#FF0000",
                    action="on",
                    flash=True,
                    embodiment="kid",
                )

        await asyncio.sleep(0.1)