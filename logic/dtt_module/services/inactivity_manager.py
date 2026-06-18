import time

from logic.dtt_module.models.enums import (
    CurrentState,
    TrialState,
)


class InactivityManager:

    def __init__(
        self,
        interaction_manager,
        timeout=12,
    ):
        self.interaction = interaction_manager
        self.timeout = timeout

    async def check(
        self,
        *,
        ctx,
        expr,
        perception,
        reset_timer,
    ):

        if (
            ctx.state != CurrentState.USER
            or ctx.trial_state not in [
                TrialState.SD,
                TrialState.PROMPTING,
                TrialState.HP_SD,
                TrialState.RETRY_SD,
            ]
        ):
            return

        elapsed = (
            time.monotonic()
            - ctx.last_activity
        )

        if (
            elapsed < self.timeout
            or ctx.prompt_given
        ):
            return

        perception.state.latest_transcript = None

        ctx.prompt_given = True

        hint_map = {
            TrialState.SD:
                "Please give the next instruction to the child.",

            TrialState.PROMPTING:
                "Please try prompting the child.",

            TrialState.HP_SD:
                "Try presenting a high probability instruction.",

            TrialState.RETRY_SD:
                "Try presenting the original instruction again.",
        }

        hint = hint_map.get(
            ctx.trial_state,
            "Please continue.",
        )

        print(f"[TIMEOUT] {hint}")

        await self.interaction.speak_text(
            expr=expr,
            text=hint,
        )

        perception.state.latest_transcript = None

        reset_timer(ctx)