# logic/dtt/state_machine/state_machine.py

from logic.dtt_module.models.enums import (
    CurrentState,
    TrialState,
)


class StateMachine:

    def __init__(
        self,
        *,
        sd_handler,
        reinforcement_handler,
        prompting_handler,
        hp_sd_handler,
        retry_sd_handler,
        kid_behavior_handler,
        feedback_handler,
    ):

        self.sd_handler = sd_handler
        self.reinforcement_handler = (
            reinforcement_handler
        )

        self.prompting_handler = (
            prompting_handler
        )

        self.hp_sd_handler = (
            hp_sd_handler
        )

        self.retry_sd_handler = (
            retry_sd_handler
        )

        self.kid_behavior_handler = (
            kid_behavior_handler
        )

        self.feedback_handler = (
            feedback_handler
        )

    async def process(
        self,
        *,
        ctx,
        expr,
        feedback,
        trial_data,
        hp_trial_data,
        sd_recognizer,
        hp_recognizer,
    ):

        #######################################################################
        # USER STATE
        #######################################################################

        if ctx.state == CurrentState.USER:

            if ctx.trial_state == TrialState.SD:

                await self.sd_handler.handle(
                    ctx=ctx,
                    feedback=feedback,
                    sd_recognizer=sd_recognizer,
                    expr=expr,
                    trial_data=trial_data,
                )

            elif (
                ctx.trial_state
                == TrialState.REINFORCEMENT
            ):

                await self.reinforcement_handler.handle(
                    ctx=ctx,
                    feedback=feedback,
                    trial_data=trial_data,
                    expr=expr,
                )

            elif (
                ctx.trial_state
                == TrialState.PROMPTING
            ):

                await self.prompting_handler.handle(
                    ctx=ctx,
                    feedback=feedback,
                    sd_recognizer=sd_recognizer,
                    expr=expr,
                )

            elif (
                ctx.trial_state
                == TrialState.HP_SD
            ):

                await self.hp_sd_handler.handle(
                    ctx=ctx,
                    feedback=feedback,
                    hp_recognizer=hp_recognizer,
                    expr=expr,
                )

            elif (
                ctx.trial_state
                == TrialState.RETRY_SD
            ):

                await self.retry_sd_handler.handle(
                    ctx=ctx,
                    feedback=feedback,
                    sd_recognizer=sd_recognizer,
                    expr=expr,
                )

        #######################################################################
        # KID STATE
        #######################################################################

        elif ctx.state == CurrentState.KID:

            if (
                ctx.trial_state
                == TrialState.KID_BEHAVIOR_1
            ):

                await (
                    self.kid_behavior_handler
                    .handle_behavior_1(
                        ctx=ctx,
                        expr=expr,
                        trial_data=trial_data,
                    )
                )

            elif (
                ctx.trial_state
                == TrialState.KID_BEHAVIOR_2
            ):

                await (
                    self.kid_behavior_handler
                    .handle_behavior_2(
                        ctx=ctx,
                        expr=expr,
                        trial_data=trial_data,
                    )
                )

            elif (
                ctx.trial_state
                == TrialState.KID_BEHAVIOR_HP
            ):

                await (
                    self.kid_behavior_handler
                    .handle_hp_behavior(
                        ctx=ctx,
                        expr=expr,
                        hp_trial_data=hp_trial_data,
                    )
                )

            elif (
                ctx.trial_state
                == TrialState.KID_BEHAVIOR_RETRY
            ):

                await (
                    self.kid_behavior_handler
                    .handle_retry_behavior(
                        ctx=ctx,
                        expr=expr,
                        trial_data=trial_data,
                    )
                )

        #######################################################################
        # TRAINER STATE
        #######################################################################

        elif ctx.state == CurrentState.TRAINER:

            if (
                ctx.trial_state
                == TrialState.FEEDBACK
            ):

                await self.feedback_handler.handle(
                    ctx=ctx,
                    expr=expr,
                    feedback=feedback,
                    trial_data=trial_data,
                )