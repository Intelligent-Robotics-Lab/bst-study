import asyncio
import json

from logic.dtt_module.models.enums import (
    CurrentState,
    TrialState,
)

from logic.feedback import evaluate_dtt_session
from logic.latin_square import get_sd_display_number

class FeedbackHandler:

    def __init__(
        self,
        interaction_manager,
        perception_agent,
        agent,
        sync
    ):
        self.interaction = interaction_manager
        self.perception_agent = perception_agent
        self.agent = agent
        self.sync = sync

    async def handle(
        self,
        *,
        ctx,
        expr,
        feedback,
        trial_data,
    ):

        # Sync client logic for data collection platofrm (gate 1: pre-feedback and post interaction)
        loop_index = get_sd_display_number(ctx.trial_sd, ctx.latin_square_configuration)
        await self.sync.kid_response_complete(loop_index, trial_name=ctx.trial_sd) # Opens post-kid response
        await self.sync.wait_for_go_ahead(scope="loop", loop_index=loop_index, checkpoint="post_kid_response")

        await self.interaction.set_led(
            expr=expr,
            color="#00FF00",
            action="off",
            flash=False,
            embodiment="kid",
        )

        await self.interaction.set_led(
            expr=expr,
            color="#FFFF00",
            action="on",
            flash=False,
            embodiment="trainer",
        )

        await asyncio.sleep(0.5)

        evaluation_payload = (
            feedback.build_evaluation_payload()
        )

        evaluation = evaluate_dtt_session(
            evaluation_payload,
            feedback.study_config
        )

        print(json.dumps(evaluation, indent=2))

        feedback_text = (
            evaluation["feedback_statement"]
        )

        feedback_placeholder = {
            "embodiment": "trainer",
            "verbal": {
                "text": feedback_text
            },
            "nonverbals": [
                {
                    "channel": "face",
                    "action": "Happy",
                    "intensity": 0.7,
                    "duration": 1.0,
                    "timing": "during",
                }
            ],
        }

        packet = expr.build(
            feedback_placeholder
        )

        await expr.execute(
            agent_type=self.agent,
            embodiment=feedback_placeholder[
                "embodiment"
            ],
            packet=packet,
        )

        sleep_time = len(feedback_text) / 50

        await asyncio.sleep(
            sleep_time + 0.3
        )

        self.perception_agent.state.latest_transcript = None

        print(feedback_text)

        await self.interaction.set_led(
            expr=expr,
            color="#FFFF00",
            action="off",
            flash=False,
            embodiment="trainer",
        )

        # Open the post-feedback handling for data collection
        await self.sync.feedback_delivered(loop_index, trial_name=ctx.trial_sd) # Opens the post-feedback
        # Wait for the go ahead response to go to the next SD
        await self.sync.wait_for_go_ahead(scope="loop", loop_index=loop_index, checkpoint="post_feedback")

        # Wait for all questionarres to be executed before the light goes green again

        await self.interaction.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        if ctx.trial_sd is not None:
            ctx.completed_sds.add(
                ctx.trial_sd
            )

        print(
            f"Completed SDs: "
            f"{ctx.completed_sds}"
        )

        if len(ctx.completed_sds) >= 6:

            final_trial = trial_data["Session Complete"]

            await self.interaction.run_behavior(
                expr=expr,
                behavior=final_trial[
                    "child_behavior"
                ],
            )

            ctx.session_complete = True

            print("You're Done")

            return

        ctx.state = CurrentState.USER
        ctx.trial_state = TrialState.SD
        ctx.session_complete = False