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
        self.interaction = (
            interaction_manager
        )
        self.perception_agent = (
            perception_agent
        )
        self.log_transcript = (
            log_transcript_callback
        )
        self.reset_inactivity_timer = (
            reset_inactivity_timer_callback
        )

    async def handle(
        self,
        *,
        ctx,
        feedback,
        trial_data,
        reinforcement_recognizer,
        expr,
    ):

        transcript = (
            self.perception_agent.state
            .latest_transcript
        )

        if transcript is not None:

            observed = {
                "verbal_text": transcript,
                "emotion": (
                    self.perception_agent.state
                    .latest_emotion
                ),
            }

            result = (
                reinforcement_recognizer.recognize(
                    observed_input=observed
                )
            )

            recognized_id = result.get(
                "matched_sd_id"
            )

            recognized_type = result.get(
                "matched_type"
            )

            # Store for feedback later
            ctx.recognized_id = (
                recognized_id
            )
            ctx.recognized_type = (
                recognized_type
            )

            print(
                f"[REINFORCEMENT RECOGNIZED] "
                f"id={recognized_id}, "
                f"type={recognized_type}"
            )

            # Not reinforcement
            

                

            self.reset_inactivity_timer(
                ctx
            )

            result_type = (
                "success"
                if recognized_type
                == "reinforcement"
                else "confirmed_error"
            )

            self.log_transcript(
                feedback=feedback,
                trial_state=ctx.trial_state,
                transcript=transcript,
                recognized_as=recognized_id,
                recognized_type=recognized_type,
                successful=(
                    recognized_type
                    == "reinforcement"
                ),
                result_type=result_type,
            )

            print(
                f"Trial SD: "
                f"{ctx.trial_sd}"
            )
            print(
                f"Current SD: "
                f"{ctx.current_sd}"
            )

            print(
                f"Reinforcement_Source: "
                f"{ctx.reinforcement_source}"
            )

            if (
                ctx.reinforcement_source
                == "prompting"
            ):

                ctx.trial_state = (
                    TrialState.HP_SD
                )

                self.perception_agent.state.latest_transcript = (
                    None
                )
                ctx.reinforcement_source = (
                    None
                )

                self.reset_inactivity_timer(
                    ctx
                )

            elif (
                ctx.reinforcement_source
                == "hp_sds"
            ):

                ctx.trial_state = (
                    TrialState.RETRY_SD
                )

                self.perception_agent.state.latest_transcript = (
                    None
                )
                ctx.reinforcement_source = (
                    None
                )

                self.reset_inactivity_timer(
                    ctx
                )

            elif (
                ctx.reinforcement_source
                in [
                    "correct",
                    "retry",
                ]
            ):

                ctx.state = (
                    CurrentState.TRAINER
                )
                ctx.trial_state = (
                    TrialState.FEEDBACK
                )

                self.perception_agent.state.latest_transcript = (
                    None
                )
                ctx.reinforcement_source = (
                    None
                )

                self.reset_inactivity_timer(
                    ctx
                )

            await (
                self.interaction
                .set_led(
                    expr=expr,
                    color="#00FF00",
                    action="off",
                    flash=False,
                    embodiment="kid",
                )
            )

            trial = trial_data[
                ctx.trial_sd
            ]

            await (
                self.interaction
                .run_behavior(
                    expr=expr,
                    behavior=trial[
                        "reinforce_behavior"
                    ],
                )
            )

            ctx.current_sd = None

        await asyncio.sleep(0.1)