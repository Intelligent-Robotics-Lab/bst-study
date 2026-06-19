import asyncio
import json

from logic.dtt_module.models.enums import (
    CurrentState,
    TrialState,
)

from logic.feedback import evaluate_dtt_session


class FeedbackHandler:

    def __init__(
        self,
        interaction_manager,
        perception_agent,
        agent,
    ):
        self.interaction = interaction_manager
        self.perception_agent = perception_agent
        self.agent = agent

    async def handle(
        self,
        *,
        ctx,
        expr,
        feedback,
        trial_data,
    ):

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

            final_trial = trial_data["SD_7"]

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