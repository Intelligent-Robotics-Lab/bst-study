import json
import asyncio
from expression_module.expression_module import ExpressionModule
# from logic.feedback import Feedback
# from logic.feedback import evaluate_dtt_session
from logic.sd_recognizer import SDRecognizer
from enum import Enum
from Perception.sample_interaction import SampleInteractionAgent
from Perception.sample_interaction import InteractionState
from Perception.perception_client import PerceptionClient
from logic.feedback import FeedbackHolder
from logic.feedback import evaluate_dtt_session
from dataclasses import dataclass, field
from logic.monitor import update_monitor
import time


class CurrentState(Enum):
    USER = "user"
    KID = "kid"
    TRAINER = "trainer"

class TrialState(Enum):
    SD = "sd"
    KID_BEHAVIOR_1 = "kid behavior 1"
    REINFORCEMENT = "reinforcement"
    PROMPTING = "prompting"
    KID_BEHAVIOR_2 = "kid behavior 2"
    HP_SD = "hp_sd"
    KID_BEHAVIOR_HP = "kid behavior HP"
    RETRY_SD = "retry sd"
    KID_BEHAVIOR_RETRY = "kid behavior retry"
    FEEDBACK = "feedback"

DTT_IN_PROGRESS = True


@dataclass
class TrialContext:
    state: CurrentState = CurrentState.USER
    trial_state: TrialState = TrialState.SD

    trial_sd: str | None = None
    current_sd: str | None = None

    reinforcement_source: str | None = None
    last_processed: str | None = None

    completed_sds: set = field(default_factory=set)

    last_activity: float = field(default_factory=time.monotonic)
    prompt_given: bool = False

    session_complete: bool = False

class SystemCommand(Enum):
    RESTART = "restart"
    WHERE_AM_I = "where_am_i"
    STOP = "stop"
    HELP = "help"
    NONE = "none"


@dataclass
class StateSnapshot:
    state: CurrentState
    trial_state: TrialState
    trial_sd: str | None
    current_sd: str | None



    


"""This class contains the logic to perform the rehearsal and feedback phases (DTT) for BST"""
class DTT:

    def __init__(self, agent=None):
        self.agent = agent
        self.hp_index = 0

        self.ctx = TrialContext(
            state=CurrentState.USER,
            trial_state=TrialState.SD,
        )

    async def wait_for_input(self, prompt="> "):
        return await asyncio.to_thread(input, prompt)

    async def wait_for_sd(self):
        print("\n[WAIT FOR SD]")
        await self.wait_for_input("Press ENTER when SD is delivered ")

    async def wait_for_reinforcement(self):
        print("\n[WAIT FOR REINFORCEMENT]")
        await self.wait_for_input("Press ENTER when reinforcement is delivered ")

    async def wait_for_prompt(self):
        print("\n[WAIT FOR PROMPT]")
        await self.wait_for_input("Press ENTER when prompt is delivered ")

    async def run_behavior(self, expr, behavior_data):

        packet = expr.build(behavior_data)

        await expr.execute(self.agent, behavior_data["embodiment"], packet)

    def get_feedback_placeholder(self, correctness):

        if correctness == "Correct":

            return {
                "embodiment": "trainer",

                "verbal": {
                    "text": "Nice job reinforcing the correct response."
                },

                "nonverbals": [
                    {
                        "channel": "face",
                        "action": "Happy",
                        "intensity": 0.7,
                        "duration": 1.0,
                        "timing": "during"
                    }
                ]
            }

        elif correctness in ["Incorrect", "No Response"]:

            return {
                "embodiment": "trainer",

                "verbal": {
                    "text": "Nice recovery using prompting and redelivery."
                },

                "nonverbals": [
                    {
                        "channel": "face",
                        "action": "Happy",
                        "intensity": 0.7,
                        "duration": 1.0,
                        "timing": "during"
                    }
                ]
            }

        return {
            "embodiment": "trainer",

            "verbal": {
                "text": "Good work."
            },

            "nonverbals": []
        }
    def detect_system_command(
        self,
        transcript: str | None,
    ) -> SystemCommand:

        if not transcript:
            return SystemCommand.NONE

        text = transcript.lower().strip()

        # Restart
        restart_phrases = [
            "restart",
            "start over",
            "reset",
            "restart trial",
        ]

        # Where am I
        where_am_i_phrases = [
            "where am i",
            "what do i do",
            "what should i do",
            "what now",
            "what next",
            "help me",
            "what step",
            "what state",
        ]

        

        if any(
            phrase in text
            for phrase in restart_phrases
        ):
            return SystemCommand.RESTART

        if any(
            phrase in text
            for phrase in where_am_i_phrases
        ):
            return SystemCommand.WHERE_AM_I

        

        return SystemCommand.NONE

    # =====================================================

    async def speak_text(
        self,
        expr,
        text: str,
    ):

        packet_data = {
            "embodiment": "trainer",
            "verbal": {
                "text": text
            },
            "nonverbals": [
                {
                    "channel": "face",
                    "action": "Happy",
                    "intensity": 0.5,
                    "duration": 1.0,
                    "timing": "during",
                }
            ],
        }

        packet = expr.build(packet_data)

        await expr.execute(
            self.agent,
            packet_data["embodiment"],
            packet,
        )

        sleep_time = (
            len(text) / 14
        ) * 1.15

        await asyncio.sleep(
            sleep_time + 0.3
        )

    # =====================================================

    def build_where_am_i_text(
        self,
        trial_state: TrialState,
        trial_sd: str | None,
    ) -> str:

        mapping = {

            TrialState.SD:
                "You should deliver the discriminative stimulus.",

            TrialState.REINFORCEMENT:
                "You should reinforce the child behavior.",

            TrialState.PROMPTING:
                "You should provide a prompt to the child.",

            TrialState.HP_SD:
                "You should deliver a high probability SD.",

            TrialState.RETRY_SD:
                "You should retry the original SD.",

            TrialState.FEEDBACK:
                "The system is currently giving feedback.",
        }

        base = mapping.get(
            trial_state,
            "You are in the session.",
        )

        if trial_sd:
            base += f" Current target is {trial_sd}."

        return base

    # =====================================================

    async def handle_system_command(
        self,
        command: SystemCommand,
        expr,
        feedback,
    ):

        global DTT_IN_PROGRESS

        if command == SystemCommand.RESTART:

            feedback.reset()

            await self.speak_text(
                expr,
                "Restarting the current trial.",
            )

            return StateSnapshot(
                state=CurrentState.USER,
                trial_state=TrialState.SD,
                trial_sd=None,
                current_sd=None,
            )

        if command == SystemCommand.WHERE_AM_I:

            explanation = (
                self.build_where_am_i_text(
                    self.current_trial_state,
                    self.current_trial_sd,
                )
            )

            await self.speak_text(
                expr,
                explanation,
            )

            return None

        if command == SystemCommand.HELP:

            help_text = (
                "You can say restart, "
                "where am I, help, or stop."
            )

            await self.speak_text(
                expr,
                help_text,
            )

            return None

        if command == SystemCommand.STOP:

            await self.speak_text(
                expr,
                "Ending the session.",
            )

            DTT_IN_PROGRESS = False

            return None

        return None
    async def execute(self):
        await self.main_dtt_loop()

    async def run_perception(self, client, agent):

        async for event in client.events():
            event_type = event.get("event_type")
            payload = event.get("payload", {})

            if event_type == "asr_update":
                agent.handle_asr(payload)

            elif event_type == "emotion_update":
                agent.handle_emotion(payload)
    def log_transcript(
        self,
        feedback,
        trial_state,
        transcript,
        recognized_as=None,
        successful=False,
    ):
        feedback.add_transcript_event(
            trial_state=trial_state.value,
            text=transcript,
            recognized_as=recognized_as,
            successful=successful,
        )
    async def handle_sd_recognition(
        self,
        *,
        transcript,
        emotion,
        recognizer,
        feedback,
        trial_state,
        expected_sd,
        next_trial_state,
        state,
        last_processed,
    ):

        if not transcript or transcript == last_processed:
            return None

        observed = {
            "verbal_text": transcript,
            "emotion": emotion,
        }

        result = recognizer.recognize(
            observed_input=observed
        )

        current_sd = result["matched_sd_id"]

        success = (
            current_sd is not None
            if expected_sd is None
            else current_sd == expected_sd
        )

        self.log_transcript(
            feedback=feedback,
            trial_state=trial_state,
            transcript=transcript,
            recognized_as=current_sd,
            successful=success,
        )

        return {
            "current_sd": current_sd,
            "success": success,
            "next_state": (
                CurrentState.KID
                if success
                else state
            ),
            "next_trial_state": (
                next_trial_state
                if success
                else trial_state
            ),
            "last_processed": transcript,
        }
    
    async def set_led(self, expr, color, action, flash, embodiment):
        turn = {
            "embodiment": "kid",
            "verbal": {
                "text": " "
            },
            "nonverbals": [
                {
                    "channel": "led",
                    "action": action,
                    "color": color,
                    "duration": 2.0
                }
            ]
        }

        packet = expr.build(turn)

        await expr.execute(
            agent_type=self.agent,
            embodiment=embodiment,
            packet=packet,
        )

        if flash:
            await asyncio.sleep(1.5)
            await self.set_led(expr=expr, color = "#00FF00", action = "on", flash=False, embodiment="kid")

        await asyncio.sleep(0.5)

    

    async def run_kid_behavior(
        self,
        expr,
        behavior,
    ):

        packet = expr.build(behavior)

        await expr.execute(
            self.agent,
            behavior["embodiment"],
            packet,
        )

        sleep_time = min(
            (len(behavior["verbal"]["text"]) / 14) * 1.15,
            3.0
        )

        await asyncio.sleep(sleep_time + 1.3)
    def update_monitor_state(
        self,
        trial_sd,
        trial_state,
        transcript,
        emotion,
        completed_sds
    ):
        update_monitor(
            screen="rehearsal",
            trial_sd=trial_sd,
            trial_state=(
                trial_state.name
                if trial_state
                else None
            ),
            transcript=transcript,
            emotion=emotion,
            completed_sds=list(completed_sds)
        )

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
    async def initialize_perception(self):

        agent = SampleInteractionAgent(
            silence_timeout=2.0
        )

        client = PerceptionClient(
            server_host="141.210.88.210",
            server_port=8000,
        )

        self.perception_agent = agent
        self.client = client

        perception_task = asyncio.create_task(
            self.run_perception(client, agent)
        )

        return perception_task
    
    def reset_inactivity_timer(self, ctx):
        ctx.last_activity = time.monotonic()
        ctx.prompt_given = False
#################################################################################
#                               SD STATE                                        #
#################################################################################

    async def handle_sd_state(
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

        transcript = self.perception_agent.state.latest_transcript
        emotion = self.perception_agent.state.latest_emotion

        print(f"[USER INPUT] transcript={transcript}")

        if (
            not transcript
            or transcript == ctx.last_processed
        ):
            await asyncio.sleep(0.1)
            return

        ctx.last_processed = transcript

        observed = {
            "verbal_text": transcript,
            "emotion": emotion,
        }

        result = sd_recognizer.recognize(
            observed_input=observed
        )

        ctx.current_sd = result["matched_sd_id"]
        ctx.trial_sd = ctx.current_sd

        if ctx.current_sd is not None:

            if ctx.current_sd in ctx.completed_sds:

                await self.handle_completed_sd(
                    ctx=ctx,
                    expr=expr,
                )
                return

        await self.process_sd_result(
            ctx=ctx,
            transcript=transcript,
            feedback=feedback,
            expr=expr,
            trial_data=trial_data,
        )

        await asyncio.sleep(0.1)

    async def handle_completed_sd(
        self,
        *,
        ctx,
        expr,
    ):

        text = (
            f"You have already completed "
            f"{ctx.current_sd}. "
            f"Please move onto a different SD."
        )

        await self.speak_text(
            expr=expr,
            text=text,
        )

        self.perception_agent.state.latest_transcript = None

        ctx.current_sd = None
        ctx.trial_sd = None

        ctx.state = CurrentState.USER
        ctx.trial_state = TrialState.SD
    async def process_sd_result(
        self,
        *,
        ctx,
        transcript,
        feedback,
        expr,
        trial_data,
    ):

        print(f"[SD DETECTED] {ctx.current_sd}")

        feedback.reset()

        self.log_transcript(
            feedback=feedback,
            trial_state=TrialState.SD,
            transcript=transcript,
            recognized_as=ctx.current_sd,
            successful=(ctx.current_sd is not None),
        )

        if ctx.current_sd is None:

            await self.set_led(
                expr=expr,
                color="#FF0000",
                action="on",
                flash=True,
                embodiment="kid",
            )

            ctx.state = CurrentState.USER
            ctx.trial_state = TrialState.SD

            return

        feedback.trial_id = ctx.current_sd
        feedback.expected_sd = (
            trial_data[ctx.current_sd]["sd"]
        )
        feedback.correctness = (
            trial_data[ctx.current_sd]["correctness"]
        )

        ctx.state = CurrentState.KID
        ctx.trial_state = TrialState.KID_BEHAVIOR_1

#################################################################################
#                          REINFORCEMENT STATE                                  #
#################################################################################
    async def handle_reinforcement_state(
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

            await self.set_led(
                expr=expr,
                color="#00FF00",
                action="off",
                flash=False,
                embodiment="kid",
            )

            trial = trial_data[ctx.trial_sd]

            await self.run_kid_behavior(
                expr,
                trial["reinforce_behavior"],
            )

            ctx.current_sd = None

        await asyncio.sleep(0.1)
#################################################################################
#                            PROPMTING STATE                                    #
#################################################################################
    async def handle_prompting_state(
        self,
        *,
        ctx,
        sd_recognizer,
        feedback,
        expr,
    ):

        await self.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        result = await self.handle_sd_recognition(
            transcript=self.perception_agent.state.latest_transcript,
            emotion=self.perception_agent.state.latest_emotion,
            recognizer=sd_recognizer,
            feedback=feedback,
            trial_state=ctx.trial_state,
            expected_sd=ctx.trial_sd,
            next_trial_state=TrialState.KID_BEHAVIOR_2,
            state=ctx.state,
            last_processed=ctx.last_processed,
        )

        if result:

            ctx.last_processed = result["last_processed"]
            ctx.current_sd = result["current_sd"]

            if result["success"]:

                self.reset_inactivity_timer(ctx)

                ctx.state = result["next_state"]
                ctx.trial_state = result["next_trial_state"]

            else:

                await self.set_led(
                    expr=expr,
                    color="#FF0000",
                    action="on",
                    flash=True,
                    embodiment="kid",
                )

        await asyncio.sleep(0.1)
#################################################################################
#                               HP SD STATE                                     #
#################################################################################
    async def handle_hp_sd_state(
        self,
        *,
        ctx,
        hp_recognizer,
        feedback,
        expr,
    ):

        await self.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        result = await self.handle_sd_recognition(
            transcript=self.perception_agent.state.latest_transcript,
            emotion=self.perception_agent.state.latest_emotion,
            recognizer=hp_recognizer,
            feedback=feedback,
            trial_state=ctx.trial_state,
            expected_sd=None,
            next_trial_state=TrialState.KID_BEHAVIOR_HP,
            state=ctx.state,
            last_processed=ctx.last_processed,
        )

        if result:

            ctx.last_processed = result["last_processed"]
            ctx.current_sd = result["current_sd"]

            if result["success"]:

                self.reset_inactivity_timer(ctx)

                ctx.state = result["next_state"]
                ctx.trial_state = result["next_trial_state"]

            else:

                await self.set_led(
                    expr=expr,
                    color="#FF0000",
                    action="on",
                    flash=True,
                    embodiment="kid",
                )

        await asyncio.sleep(0.1)
#################################################################################
#                            RETRY SD STATE                                     #
#################################################################################
    async def handle_retry_sd_state(
        self,
        *,
        ctx,
        sd_recognizer,
        feedback,
        expr,
    ):

        await self.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        result = await self.handle_sd_recognition(
            transcript=self.perception_agent.state.latest_transcript,
            emotion=self.perception_agent.state.latest_emotion,
            recognizer=sd_recognizer,
            feedback=feedback,
            trial_state=ctx.trial_state,
            expected_sd=ctx.trial_sd,
            next_trial_state=TrialState.KID_BEHAVIOR_RETRY,
            state=ctx.state,
            last_processed=ctx.last_processed,
        )

        if result:

            ctx.last_processed = result["last_processed"]
            ctx.current_sd = result["current_sd"]

            if result["success"]:

                self.reset_inactivity_timer(ctx)

                ctx.state = result["next_state"]
                ctx.trial_state = result["next_trial_state"]

            else:

                await self.set_led(
                    expr=expr,
                    color="#FF0000",
                    action="on",
                    flash=True,
                    embodiment="kid",
                )

        await asyncio.sleep(0.1)
#################################################################################
#                            KID BEHAVIOR 1 STATE                               #
#################################################################################
    async def handle_kid_behavior_1(
        self,
        *,
        ctx,
        expr,
        trial_data,
    ):

        await self.set_led(
            expr=expr,
            color="#00FF00",
            action="off",
            flash=False,
            embodiment="kid",
        )

        trial = trial_data[ctx.current_sd]

        await self.run_kid_behavior(
            expr,
            trial["child_behavior"],
        )

        ctx.state = CurrentState.USER

        if trial["correctness"] == "Correct":

            ctx.reinforcement_source = "correct"
            ctx.trial_state = TrialState.REINFORCEMENT

        elif trial["correctness"] == "No Response":

            ctx.reinforcement_source = None
            ctx.trial_state = TrialState.PROMPTING

            self.reset_inactivity_timer(ctx)

        await self.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        await asyncio.sleep(0.1)

        self.perception_agent.state.latest_transcript = None

        await asyncio.sleep(0.1)
#################################################################################
#                            KID BEHAVIOR 2 STATE                               #
#################################################################################
    async def handle_kid_behavior_2(
        self,
        *,
        ctx,
        expr,
        trial_data,
    ):

        await self.set_led(
            expr=expr,
            color="#00FF00",
            action="off",
            flash=False,
            embodiment="kid",
        )

        trial = trial_data[ctx.current_sd]

        await self.run_kid_behavior(
            expr,
            trial["prompted_behavior"],
        )

        ctx.state = CurrentState.USER
        ctx.trial_state = TrialState.REINFORCEMENT
        ctx.reinforcement_source = "prompting"
        self.reset_inactivity_timer(ctx)

        await self.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        await asyncio.sleep(0.1)

        self.perception_agent.state.latest_transcript = None

        await asyncio.sleep(0.1)
#################################################################################
#                          KID BEHAVIOR HP SD STATE                             #
#################################################################################
    async def handle_kid_behavior_hp(
        self,
        *,
        ctx,
        expr,
        hp_trial_data,
    ):

        await self.set_led(
            expr=expr,
            color="#00FF00",
            action="off",
            flash=False,
            embodiment="kid",
        )

        hp_trial = hp_trial_data[ctx.current_sd]

        await self.run_kid_behavior(
            expr,
            hp_trial["child_behavior"],
        )

        self.reset_inactivity_timer(ctx)
        await self.set_led(
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

        # HP SD is finished, clear current match
        ctx.current_sd = None
#################################################################################
#                          KID BEHAVIOR RETRY STATE                             #
#################################################################################
    async def handle_kid_behavior_retry(
        self,
        *,
        ctx,
        expr,
        trial_data,
    ):

        await self.set_led(
            expr=expr,
            color="#00FF00",
            action="off",
            flash=False,
            embodiment="kid",
        )

        trial = trial_data[ctx.current_sd]

        await self.run_kid_behavior(
            expr,
            trial["retry_behavior"],
        )
        self.reset_inactivity_timer(ctx)
        await self.set_led(
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
#################################################################################
#                          TRAINER FEEDBACK STATE                               #
#################################################################################        

    async def handle_feedback_state(
        self,
        *,
        ctx,
        expr,
        feedback,
        trial_data,
    ):

        await self.set_led(
            expr=expr,
            color="#00FF00",
            action="off",
            flash=False,
            embodiment="kid",
        )

        await self.set_led(
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
            evaluation_payload
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
            embodiment=feedback_placeholder["embodiment"],
            packet=packet,
        )

        sleep_time = len(feedback_text) / 50

        await asyncio.sleep(
            sleep_time + 0.3
        )

        self.perception_agent.state.latest_transcript = None

        print(feedback_text)

        await self.set_led(
            expr=expr,
            color="#FFFF00",
            action="off",
            flash=False,
            embodiment="trainer",
        )

        await self.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        if ctx.trial_sd is not None:
            ctx.completed_sds.add(ctx.trial_sd)

        print(
            f"Completed SDs: {ctx.completed_sds}"
        )

        if len(ctx.completed_sds) >= 6:

            final_trial = trial_data["SD_7"]

            await self.run_kid_behavior(
                expr=expr,
                behavior=final_trial["child_behavior"],
            )

            ctx.session_complete = True

            print("You're Done")

            return

        ctx.state = CurrentState.USER
        ctx.trial_state = TrialState.SD
        ctx.session_complete = False
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

        perception_task = (
            await self.initialize_perception()
        )

        await self.set_led(
            expr=expr,
            color="#00FF00",
            action="on",
            flash=False,
            embodiment="kid",
        )

        

        try:

            while DTT_IN_PROGRESS:

                # -------------------------
                # Context Refresh
                # -------------------------

                ctx.transcript = (
                    self.perception_agent.state.latest_transcript
                )

                ctx.emotion = (
                    self.perception_agent.state.latest_emotion
                )

                print(
                    f"\n[STATE] {ctx.state} | {ctx.trial_state}"
                )

                print(
                    f"[TRACK] trial_sd={ctx.trial_sd} "
                    f"current_sd={ctx.current_sd}"
                )

                self.current_trial_state = ctx.trial_state
                self.current_trial_sd = ctx.trial_sd

                # -------------------------
                # Trainer inactivity timeout
                # -------------------------

                WAIT_TIMEOUT = 12

                if (
                    ctx.state == CurrentState.USER
                    and ctx.trial_state in [
                        TrialState.SD,
                        TrialState.PROMPTING,
                        TrialState.HP_SD,
                        TrialState.RETRY_SD,
                    ]
                ):

                    elapsed = (
                        time.monotonic()
                        - ctx.last_activity
                    )

                    if (
                        elapsed >= WAIT_TIMEOUT
                        and not ctx.prompt_given
                    ):

                        self.perception_agent.state.latest_transcript = None

                        ctx.prompt_given = True

                        if ctx.trial_state == TrialState.SD:
                            hint = (
                                "Please give the next instruction "
                                "to the child."
                            )

                        elif ctx.trial_state == TrialState.PROMPTING:
                            hint = (
                                "Please try prompting the child?"
                            )

                        elif ctx.trial_state == TrialState.HP_SD:
                            hint = (
                                "Try presenting a high "
                                "probability instruction."
                            )

                        elif ctx.trial_state == TrialState.RETRY_SD:
                            hint = (
                                "Try presenting the original "
                                "instruction again."
                            )

                        print(f"[TIMEOUT] {hint}")

                        await self.speak_text(
                            expr=expr,
                            text=hint,
                        )

                        self.perception_agent.state.latest_transcript = None

                        self.reset_inactivity_timer(ctx)

                # -------------------------
                # System Commands
                # -------------------------

                command = self.detect_system_command(
                    ctx.transcript
                )

                self.update_monitor_state(
                    trial_sd=ctx.trial_sd,
                    trial_state=ctx.trial_state,
                    transcript=ctx.transcript,
                    emotion=ctx.emotion,
                    completed_sds=ctx.completed_sds,
                )

                if command != SystemCommand.NONE:

                    await self.set_led(
                        expr=expr,
                        color="#0000FF",
                        action="on",
                        flash=False,
                        embodiment="trainer",
                    )

                    result = await self.handle_system_command(
                        command=command,
                        expr=expr,
                        feedback=feedback,
                    )

                    self.perception_agent.state.latest_transcript = None
                    ctx.last_processed = None

                    if isinstance(result, StateSnapshot):

                        ctx.state = result.state
                        ctx.trial_state = result.trial_state
                        ctx.trial_sd = result.trial_sd
                        ctx.current_sd = result.current_sd

                    await self.set_led(
                        expr=expr,
                        color="#0000FF",
                        action="off",
                        flash=False,
                        embodiment="trainer",
                    )

                    continue

                # -------------------------
                # USER STATE
                # -------------------------

                if ctx.state == CurrentState.USER:

                    if ctx.trial_state == TrialState.SD:

                        await self.handle_sd_state(
                            ctx=ctx,
                            feedback=feedback,
                            sd_recognizer=sd_recognizer,
                            expr=expr,
                            trial_data=trial_data,
                        )

                    elif ctx.trial_state == TrialState.REINFORCEMENT:

                        await self.handle_reinforcement_state(
                            ctx=ctx,
                            feedback=feedback,
                            trial_data=trial_data,
                            expr=expr,
                        )

                    elif ctx.trial_state == TrialState.PROMPTING:

                        await self.handle_prompting_state(
                            ctx=ctx,
                            feedback=feedback,
                            sd_recognizer=sd_recognizer,
                            expr=expr,
                        )

                    elif ctx.trial_state == TrialState.HP_SD:

                        await self.handle_hp_sd_state(
                            ctx=ctx,
                            feedback=feedback,
                            hp_recognizer=hp_recognizer,
                            expr=expr,
                        )

                    elif ctx.trial_state == TrialState.RETRY_SD:

                        await self.handle_retry_sd_state(
                            ctx=ctx,
                            feedback=feedback,
                            sd_recognizer=sd_recognizer,
                            expr=expr,
                        )

                # -------------------------
                # KID STATE
                # -------------------------

                elif ctx.state == CurrentState.KID:

                    if ctx.trial_state == TrialState.KID_BEHAVIOR_1:

                        await self.handle_kid_behavior_1(
                            ctx=ctx,
                            expr=expr,
                            trial_data=trial_data,
                        )

                    elif ctx.trial_state == TrialState.KID_BEHAVIOR_2:

                        await self.handle_kid_behavior_2(
                            ctx=ctx,
                            expr=expr,
                            trial_data=trial_data,
                        )

                    elif ctx.trial_state == TrialState.KID_BEHAVIOR_HP:

                        await self.handle_kid_behavior_hp(
                            ctx=ctx,
                            expr=expr,
                            hp_trial_data=hp_trial_data,
                        )

                    elif (
                        ctx.trial_state
                        == TrialState.KID_BEHAVIOR_RETRY
                    ):

                        await self.handle_kid_behavior_retry(
                            ctx=ctx,
                            expr=expr,
                            trial_data=trial_data,
                        )

                # -------------------------
                # TRAINER STATE
                # -------------------------

                elif ctx.state == CurrentState.TRAINER:

                    if ctx.trial_state == TrialState.FEEDBACK:

                        await self.handle_feedback_state(
                            ctx=ctx,
                            expr=expr,
                            feedback=feedback,
                            trial_data=trial_data,
                        )

                        if ctx.session_complete:
                            DTT_IN_PROGRESS = False

        finally:

            perception_task.cancel()

        
       
def __main__():
    DTT.main_dtt_loop()