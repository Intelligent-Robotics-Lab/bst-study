import json
import asyncio
from expression_module.expression_module import ExpressionModule
from logic.sd_recognizer import SDRecognizer
from enum import Enum
from perception.sample_interaction import SampleInteractionAgent
from perception.sample_interaction import InteractionState
from perception.perception_client import PerceptionClient
from logic.feedback import FeedbackHolder
from logic.dtt_module.session.interaction_manager import InteractionManager
import time
from logic.dtt_module.handlers.sd_handler import SDHandler
from expression_module.expression_module import ExpressionModule

from logic.sd_recognizer import SDRecognizer
from logic.feedback import FeedbackHolder
from logic.monitor import update_monitor

from logic.dtt_module.models.trial_context import TrialContext
from logic.dtt_module.models.enums import (
    CurrentState,
    TrialState,
    SystemCommand,
)
from logic.dtt_module.models.state_snapshot import (
    StateSnapshot,
)
from logic.dtt_module.handlers.sd_processing_handler import (
    SDProcessingHandler,
)

# Managers
from logic.dtt_module.session.interaction_manager import (
    InteractionManager,
)
from logic.dtt_module.services.perception_manager import (
    PerceptionManager,
)
from logic.dtt_module.commands.command_manager import (
    CommandManager,
)
from logic.dtt_module.services.context_manager import (
    ContextManager,
)
from logic.dtt_module.services.inactivity_manager import (
    InactivityManager,
)

# Services
from logic.dtt_module.services.transcript_logger import (
    TranscriptLogger,
)
from logic.dtt_module.handlers.sd_recognition_handler import (
    SDRecognitionHandler,
)

# Handlers
from logic.dtt_module.handlers.sd_handler import (
    SDHandler,
)
from logic.dtt_module.handlers.reinforcement_handler import (
    ReinforcementHandler,
)
from logic.dtt_module.handlers.prompting_handler import (
    PromptingHandler,
)
from logic.dtt_module.handlers.hp_sd_handler import (
    HPSDHandler,
)
from logic.dtt_module.handlers.retry_sd_handler import (
    RetrySDHandler,
)
from logic.dtt_module.handlers.kid_behavior_handler import (
    KidBehaviorHandler,
)
from logic.dtt_module.handlers.feedback_handler import (
    FeedbackHandler,
)

from logic.dtt_module.state_machine.state_machine import (
    StateMachine,
)
DTT_IN_PROGRESS = True
"""This class contains the logic to perform the rehearsal and feedback phases (DTT) for BST"""
class DTT:

    def __init__(self, agent=None, study_config=None):

        self.agent = agent
        self.study_config = study_config

        # --------------------------------------------------
        # Managers
        # --------------------------------------------------

        self.interaction = InteractionManager(
            agent=self.agent
        )

        self.perception = PerceptionManager()

        self.command_manager = CommandManager(
            interaction_manager=self.interaction,
        )

        self.context_manager = ContextManager()

        self.inactivity_manager = InactivityManager(
            interaction_manager=self.interaction,
        )

        # --------------------------------------------------
        # Services
        # --------------------------------------------------

        self.transcript_logger = TranscriptLogger()

        self.sd_recognition_handler = (
            SDRecognitionHandler(
                log_transcript_callback=
                    self.transcript_logger.log
            )
        )

        self.sd_processing_handler = (
            SDProcessingHandler(
                interaction_manager=
                    self.interaction,
                perception_agent=
                    self.perception,
                log_transcript_callback=
                    self.transcript_logger.log,
            )
        )

        # --------------------------------------------------
        # State Handlers
        # --------------------------------------------------

        self.sd_handler = SDHandler(
            interaction_manager=
                self.interaction,
            perception_agent= 
            self.perception,
            sd_processing_handler=
            self.sd_processing_handler,
        )

        self.reinforcement_handler = (
            ReinforcementHandler(
                interaction_manager=
                    self.interaction,
                perception_agent=
                    self.perception,
                log_transcript_callback=
                    self.transcript_logger.log,
                reset_inactivity_timer_callback=
                    self.reset_inactivity_timer,
            )
        )

        self.prompting_handler = (
            PromptingHandler(
                interaction_manager=
                    self.interaction,
                perception_agent=
                    self.perception,
                sd_recognition_handler=
                    self.sd_recognition_handler,
                reset_inactivity_timer_callback=
                    self.reset_inactivity_timer,
            )
        )

        self.hp_sd_handler = (
            HPSDHandler(
                interaction_manager=
                    self.interaction,
                perception_agent=
                    self.perception,
                sd_recognition_handler=
                    self.sd_recognition_handler,
                reset_inactivity_timer_callback=
                    self.reset_inactivity_timer,
            )
        )

        self.retry_sd_handler = (
            RetrySDHandler(
                interaction_manager=
                    self.interaction,
                perception_agent=
                    self.perception,
                sd_recognition_handler=
                    self.sd_recognition_handler,
                reset_inactivity_timer_callback=
                    self.reset_inactivity_timer,
            )
        )

        self.kid_behavior_handler = (
            KidBehaviorHandler(
                interaction_manager=
                    self.interaction,
                perception_agent=
                    self.perception,
                reset_inactivity_timer_callback=
                    self.reset_inactivity_timer,
            )
        )

        self.feedback_handler = (
            FeedbackHandler(
                interaction_manager=
                    self.interaction,
                perception_agent=
                    self.perception,
                agent=self.agent,
            )
        )

        # --------------------------------------------------
        # State Machine
        # --------------------------------------------------

        self.state_machine = StateMachine(
            sd_handler=self.sd_handler,
            reinforcement_handler=
                self.reinforcement_handler,
            prompting_handler=
                self.prompting_handler,
            hp_sd_handler=
                self.hp_sd_handler,
            retry_sd_handler=
                self.retry_sd_handler,
            kid_behavior_handler=
                self.kid_behavior_handler,
            feedback_handler=
                self.feedback_handler,
        )

        # --------------------------------------------------
        # Context
        # --------------------------------------------------

        self.ctx = TrialContext(
            state=CurrentState.USER,
            trial_state=TrialState.SD,
        )

    async def execute(self):
        await self.main_dtt_loop()


    def load_trial_data(self):

        with open("data/trial_data.json", "r") as f:
            trial_data = json.load(f)["trial_data"]

        with open("data/hp_trial_data.json", "r") as f:
            hp_trial_data = json.load(f)["hp_trial_data"]

        return trial_data, hp_trial_data
    
    def initialize_runtime(
        self,
        trial_data,
        hp_trial_data,
    ):

        expr = ExpressionModule()

        sd_recognizer = SDRecognizer(
            trial_data=trial_data
        )

        hp_recognizer = SDRecognizer(
            trial_data=hp_trial_data
        )

        feedback = FeedbackHolder()

        return (
            expr,
            sd_recognizer,
            hp_recognizer,
            feedback,
        )
    
    def reset_inactivity_timer(self, ctx):
        ctx.last_activity = time.monotonic()
        ctx.prompt_given = False

#################################################################################
#                           MAIN DTT LOOP                                       #
#################################################################################




    async def main_dtt_loop(self):

        ctx = self.ctx

        global DTT_IN_PROGRESS

        trial_data, hp_trial_data = (
            self.load_trial_data()
        )

        (
            expr,
            sd_recognizer,
            hp_recognizer,
            feedback,
        ) = self.initialize_runtime(
            trial_data,
            hp_trial_data,
        )

        await self.perception.start()

        await self.interaction.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        try:

            while DTT_IN_PROGRESS:

                # ---------------------------------
                # Refresh Context
                # ---------------------------------

                self.context_manager.refresh(
                    ctx=ctx,
                    perception=self.perception,
                )

                # ---------------------------------
                # Monitor
                # ---------------------------------

                update_monitor(
                    trial_sd=ctx.trial_sd,
                    trial_state=ctx.trial_state,
                    transcript=ctx.transcript,
                    emotion=ctx.emotion,
                    completed_sds=ctx.completed_sds,
                )

                # ---------------------------------
                # Timeout Handling
                # ---------------------------------

                await self.inactivity_manager.check(
                    ctx=ctx,
                    expr=expr,
                    perception=self.perception,
                    reset_timer=self.reset_inactivity_timer,
                )

                # ---------------------------------
                # System Commands
                # ---------------------------------

                command = (
                    self.command_manager
                    .detect_system_command(
                        ctx.transcript
                    )
                )

                if command != SystemCommand.NONE:

                    result = (
                        await self.command_manager
                        .handle_system_command(
                            command=command,
                            expr=expr,
                            feedback=feedback,
                            current_trial_state=
                                ctx.trial_state,
                            current_trial_sd=
                                ctx.trial_sd,
                        )
                    )

                    self.perception.state.latest_transcript = None
                    ctx.last_processed = None

                    if isinstance(
                        result,
                        StateSnapshot,
                    ):
                        ctx.state = result.state
                        ctx.trial_state = (
                            result.trial_state
                        )
                        ctx.trial_sd = (
                            result.trial_sd
                        )
                        ctx.current_sd = (
                            result.current_sd
                        )

                    continue

                # ---------------------------------
                # State Machine
                # ---------------------------------

                await self.state_machine.process(
                    ctx=ctx,
                    expr=expr,
                    feedback=feedback,
                    trial_data=trial_data,
                    hp_trial_data=hp_trial_data,
                    sd_recognizer=sd_recognizer,
                    hp_recognizer=hp_recognizer,
                )

                # ---------------------------------
                # Session Complete
                # ---------------------------------

                if ctx.session_complete:
                    DTT_IN_PROGRESS = False

                await asyncio.sleep(0.1)

        finally:

            await self.perception.stop()

        
       
def __main__():
    DTT.main_dtt_loop()