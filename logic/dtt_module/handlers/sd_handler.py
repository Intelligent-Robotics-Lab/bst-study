from logic.dtt_module.models.enums import (
    CurrentState,
    TrialState,
)


class SDHandler:

    def __init__(
        self,
        interaction_manager,
        perception_agent,
        sd_processing_handler,
    ):
        self.interaction = interaction_manager
        self.perception_agent = (
            perception_agent
        )
        self.sd_processing_handler = (
            sd_processing_handler
        )

    async def handle(
        self,
        *,
        ctx,
        feedback,
        sd_recognizer,
        expr,
        trial_data,
    ):

        feedback.user_utterances = []
        feedback.child_utterances = []

        ctx.trial_sd = None
        ctx.current_sd = None

        transcript = (
            self.perception_agent.state
            .latest_transcript
        )

        emotion = (
            self.perception_agent.state
            .latest_emotion
        )

        print(
            f"[USER INPUT] "
            f"transcript={transcript}"
        )

        if (
            not transcript
            or transcript
            == ctx.last_processed
        ):
            return

        ctx.last_processed = (
            transcript
        )

        observed = {
            "verbal_text": transcript,
            "emotion": emotion,
        }

        result = (
            sd_recognizer.recognize(
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
            f"[RECOGNIZED] "
            f"id={recognized_id}, "
            f"type={recognized_type}"
        )

        # Only actual trial SDs should
        # become current_sd.
        if (
            recognized_type == "sd"
            and recognized_id in trial_data
        ):
            ctx.current_sd = (
                recognized_id
            )
            ctx.trial_sd = (
                recognized_id
            )
        else:
            ctx.current_sd = None
            ctx.trial_sd = None

        # ------------------------------------
        # No valid trial SD recognized
        # ------------------------------------

        if ctx.current_sd is None:

            await self.interaction.set_led(
                expr=expr,
                color="#FF0000",
                action="on",
                flash=True,
                embodiment="kid",
            )

            return

        # ------------------------------------
        # SD Already Completed
        # ------------------------------------

        if (
            ctx.current_sd
            in ctx.completed_sds
        ):

            print(
                f"[REPEATED SD] "
                f"{ctx.current_sd}"
            )

            await (
                self.sd_processing_handler
                .handle_completed_sd(
                    ctx=ctx,
                    expr=expr,
                )
            )

            return

        # ------------------------------------
        # Valid New SD
        # ------------------------------------

        await (
            self.sd_processing_handler
            .process_sd_result(
                ctx=ctx,
                transcript=transcript,
                feedback=feedback,
                expr=expr,
                trial_data=trial_data,
            )
        )