import asyncio

from logic.dtt_module.models.enums import (
    CurrentState,
    TrialState,
)


class ReinforcementHandler:

    def __init__(
        self,
        interaction_manager,
        perception_agent,
        log_transcript_callback,
        reset_inactivity_timer_callback,
    ):
        self.interaction = interaction_manager
        self.perception_agent = perception_agent
        self.log_transcript = log_transcript_callback
        self.reset_inactivity_timer = (
            reset_inactivity_timer_callback
        )

    async def handle(
        self,
        *,
        ctx,
        feedback,
        trial_data,
        expr,
    ):

        transcript = (
            self.perception_agent.state.latest_transcript
        )

        if transcript is not None:

            self.reset_inactivity_timer(ctx)

            self.log_transcript(
                feedback=feedback,
                trial_state=ctx.trial_state,
                transcript=transcript,
                recognized_as=ctx.current_sd,
                successful=(ctx.current_sd is not None),
            )

            print(f"Trial SD: {ctx.trial_sd}")
            print(f"Current SD: {ctx.current_sd}")

            print(
                f"Reinforcement_Source: "
                f"{ctx.reinforcement_source}"
            )

            if ctx.reinforcement_source == "prompting":

                ctx.trial_state = TrialState.HP_SD

                self.perception_agent.state.latest_transcript = None
                ctx.reinforcement_source = None

                self.reset_inactivity_timer(ctx)

            elif ctx.reinforcement_source == "hp_sds":

                ctx.trial_state = TrialState.RETRY_SD

                self.perception_agent.state.latest_transcript = None
                ctx.reinforcement_source = None

                self.reset_inactivity_timer(ctx)

            elif ctx.reinforcement_source in [
                "correct",
                "retry",
            ]:

                ctx.state = CurrentState.TRAINER
                ctx.trial_state = TrialState.FEEDBACK

                self.perception_agent.state.latest_transcript = None
                ctx.reinforcement_source = None

                self.reset_inactivity_timer(ctx)

            await self.interaction.set_led(
                expr=expr,
                color="#00FF00",
                action="off",
                flash=False,
                embodiment="kid",
            )

            trial = trial_data[ctx.trial_sd]

            await self.interaction.run_behavior(
                expr=expr,
                behavior=trial["reinforce_behavior"],
            )

            ctx.current_sd = None

        await asyncio.sleep(0.1)