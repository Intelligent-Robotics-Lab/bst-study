import asyncio

from logic.dtt_module.models.enums import (
    CurrentState,
    TrialState,
)


class KidBehaviorHandler:

    def __init__(
        self,
        interaction_manager,
        perception_agent,
        reset_inactivity_timer_callback,
    ):
        self.interaction = interaction_manager
        self.perception_agent = perception_agent
        self.reset_inactivity_timer = (
            reset_inactivity_timer_callback
        )

    async def handle_behavior_1(
        self,
        *,
        ctx,
        expr,
        trial_data,
    ):

        await self.interaction.set_led(
            expr=expr,
            color="#00FF00",
            action="off",
            flash=False,
            embodiment="kid",
        )

        trial = trial_data[ctx.current_sd]

        await self.interaction.run_behavior(
            expr=expr,
            behavior=trial["child_behavior"],
        )

        ctx.state = CurrentState.USER

        if trial["correctness"] == "Correct":

            ctx.reinforcement_source = "correct"
            ctx.trial_state = TrialState.REINFORCEMENT

        elif trial["correctness"] == "No Response":

            ctx.reinforcement_source = None
            ctx.trial_state = TrialState.PROMPTING

            self.reset_inactivity_timer(ctx)

        await self.interaction.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        await asyncio.sleep(0.1)

        self.perception_agent.state.latest_transcript = None

        await asyncio.sleep(0.1)

    async def handle_behavior_2(
        self,
        *,
        ctx,
        expr,
        trial_data,
    ):

        await self.interaction.set_led(
            expr=expr,
            color="#00FF00",
            action="off",
            flash=False,
            embodiment="kid",
        )

        trial = trial_data[ctx.current_sd]

        await self.interaction.run_behavior(
            expr=expr,
            behavior=trial["prompted_behavior"],
        )

        ctx.state = CurrentState.USER
        ctx.trial_state = TrialState.REINFORCEMENT
        ctx.reinforcement_source = "prompting"

        self.reset_inactivity_timer(ctx)

        await self.interaction.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        await asyncio.sleep(0.1)

        self.perception_agent.state.latest_transcript = None

        await asyncio.sleep(0.1)

    async def handle_hp_behavior(
        self,
        *,
        ctx,
        expr,
        hp_trial_data,
    ):

        await self.interaction.set_led(
            expr=expr,
            color="#00FF00",
            action="off",
            flash=False,
            embodiment="kid",
        )

        hp_trial = hp_trial_data[ctx.current_sd]

        await self.interaction.run_behavior(
            expr=expr,
            behavior=hp_trial["child_behavior"],
        )

        self.reset_inactivity_timer(ctx)

        await self.interaction.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        await asyncio.sleep(0.1)

        self.perception_agent.state.latest_transcript = None

        await asyncio.sleep(0.1)

        ctx.state = CurrentState.USER
        ctx.trial_state = TrialState.REINFORCEMENT
        ctx.reinforcement_source = "hp_sds"

        ctx.current_sd = None

    async def handle_retry_behavior(
        self,
        *,
        ctx,
        expr,
        trial_data,
    ):

        await self.interaction.set_led(
            expr=expr,
            color="#00FF00",
            action="off",
            flash=False,
            embodiment="kid",
        )

        trial = trial_data[ctx.current_sd]

        await self.interaction.run_behavior(
            expr=expr,
            behavior=trial["retry_behavior"],
        )

        self.reset_inactivity_timer(ctx)

        await self.interaction.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        await asyncio.sleep(0.1)

        self.perception_agent.state.latest_transcript = None

        await asyncio.sleep(0.1)

        ctx.state = CurrentState.USER
        ctx.trial_state = TrialState.REINFORCEMENT
        ctx.reinforcement_source = "retry"