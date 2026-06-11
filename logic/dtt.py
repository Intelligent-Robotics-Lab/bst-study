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
from dataclasses import dataclass
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

    async def turn_on_green_led(self, expr):

        turn = {
            "embodiment": "kid",
            "verbal": {
                "text": " "
            },
            "nonverbals": [
                {
                    "channel": "led",
                    "action": "on",
                    "color": "#00FF00",
                    "duration": 2.0
                }
            ]
        }

        packet = expr.build(turn)

        await expr.execute(
            agent_type=self.agent,
            embodiment="kid",
            packet=packet,
        )

        await asyncio.sleep(0.5)
    async def turn_off_green_led(self, expr):

        turn = {
            "embodiment": "kid",
            "verbal": {
                "text": " "
            },
            "nonverbals": [
                {
                    "channel": "led",
                    "action": "off",
                    "color": "#00FF00",
                    "duration": 2.0
                }
            ]
        }

        packet = expr.build(turn)

        await expr.execute(
            agent_type=self.agent,
            embodiment="kid",
            packet=packet,
        )

        await asyncio.sleep(0.5)
    async def turn_on_blue_led(self, expr):

        turn = {
            "embodiment": "trainer",
            "verbal": {
                "text": " "
            },
            "nonverbals": [
                {
                    "channel": "led",
                    "action": "on",
                    "color": "#0000FF",
                    "duration": 2.0
                }
            ]
        }

        packet = expr.build(turn)

        await expr.execute(
            agent_type=self.agent,
            embodiment="trainer",
            packet=packet,
        )

        await asyncio.sleep(0.5)
    async def turn_off_blue_led(self, expr):

        turn = {
            "embodiment": "kid",
            "verbal": {
                "text": " "
            },
            "nonverbals": [
                {
                    "channel": "led",
                    "action": "off",
                    "color": "#0000FF",
                    "duration": 2.0
                }
            ]
        }

        packet = expr.build(turn)

        await expr.execute(
            agent_type=self.agent,
            embodiment="trainer",
            packet=packet,
        )

        await asyncio.sleep(0.5)
       
    async def flash_red_led(self, expr):

        turn = {
            "embodiment": "kid",
            "verbal": {
                "text": " "
            },
            "nonverbals": [
                {
                    "channel": "led",
                    "action": "on",
                    "color": "#FF0000",
                    "duration": 2.0
                }
            ]
        }

        packet = expr.build(turn)

        await expr.execute(
            agent_type=self.agent,
            embodiment="kid",
            packet=packet,
        )

        await asyncio.sleep(1)
        

        await self.turn_on_green_led(expr=expr)

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

         
#################################################################################
#                           MAIN DTT LOOP                                       #
#################################################################################




    async def main_dtt_loop(self):
        global DTT_IN_PROGRESS

        last_activity = time.monotonic()
        prompt_given = False

        def reset_inactivity_timer():
            nonlocal last_activity, prompt_given
            last_activity = time.monotonic()
            prompt_given = False
        state = CurrentState.USER
        trial_state = TrialState.SD 
        trial_sd = None
        current_sd = None
        reinforcement_source = None
        completed_sds = set()
        with open("data/trial_data.json", "r") as f:
            trial_data = json.load(f)["trial_data"]

        with open("data/hp_trial_data.json", "r") as f:
            hp_trial_data = json.load(f)["hp_trial_data"]
        
        expr = ExpressionModule()
        sd_recognizer = SDRecognizer(trial_data=trial_data)
        hp_recognizer = SDRecognizer(trial_data=hp_trial_data)
        agent = SampleInteractionAgent(silence_timeout=2.0)
        feedback = FeedbackHolder()
        client = PerceptionClient(
            server_host="141.210.88.210",
            server_port=8000
        )

        # start perception in background
        perception_task = asyncio.create_task(
            self.run_perception(client, agent)
        )

        last_processed = None
        
        await self.turn_on_green_led(expr=expr)

        

        try:

            while DTT_IN_PROGRESS:
                
                # Debug print
                print(f"\n[STATE] {state} | {trial_state}")
                print(f"[TRACK] trial_sd={trial_sd} current_sd={current_sd}")
                self.current_trial_state = trial_state
                self.current_trial_sd = trial_sd
                transcript = agent.state.latest_transcript
                emotion = agent.state.latest_emotion

                # ----------------------------------
                # Trainer inactivity timeout
                # ----------------------------------

                WAIT_TIMEOUT = 15

                if (
                    state == CurrentState.USER
                    and trial_state in [
                        TrialState.SD,
                        TrialState.PROMPTING,
                        TrialState.HP_SD,
                        TrialState.RETRY_SD,
                    ]
                ):

                    elapsed = time.monotonic() - last_activity

                    if elapsed >= WAIT_TIMEOUT and not prompt_given:
                        agent.state.latest_transcript = None

                        prompt_given = True

                        if trial_state == TrialState.SD:
                            hint = "Please give the next instruction to the child."

                        elif trial_state == TrialState.PROMPTING:
                            hint = "Please try prompting the child?"

                        elif trial_state == TrialState.HP_SD:
                            hint = "Try presenting a high probability instruction."

                        elif trial_state == TrialState.RETRY_SD:
                            hint = "Try presenting the original instruction again."

                        print(f"[TIMEOUT] {hint}")

                        await self.speak_text(
                            expr=expr,
                            text=hint
                        )
                        agent.state.latest_transcript = None

                command = self.detect_system_command(
                    transcript
                )

                self.update_monitor_state(trial_sd=trial_sd, trial_state=trial_state, transcript=transcript, emotion=emotion, completed_sds=completed_sds)

                if command != SystemCommand.NONE:

                    await self.turn_on_blue_led(expr=expr)
                    result = await self.handle_system_command(
                        command=command,
                        expr=expr,
                        feedback=feedback,
                    )

                    # Clear transcript so command
                    # doesn't repeatedly trigger
                    agent.state.latest_transcript = None
                    last_processed = None

                    if isinstance(
                        result,
                        StateSnapshot,
                    ):

                        state = result.state
                        trial_state = (
                            result.trial_state
                        )
                        trial_sd = (
                            result.trial_sd
                        )
                        current_sd = (
                            result.current_sd
                        )

                    await self.turn_off_blue_led(expr=expr)
                    continue

                # -------------------------
                # USER STATE
                # -------------------------
                if state == CurrentState.USER:

                    if trial_state == TrialState.SD:
                        feedback.user_utterances = []
                        feedback.child_utterances = []
                        trial_sd = None
                       
                        transcript = agent.state.latest_transcript
                        emotion = agent.state.latest_emotion

                        print(f"[USER INPUT] transcript={transcript}")

                        if transcript and transcript != last_processed:
                            reset_inactivity_timer()
                            last_processed = transcript

                            observed = {
                                "verbal_text": transcript,
                                "emotion": emotion
                            }

                            result = sd_recognizer.recognize(
                                observed_input=observed
                            )

                            current_sd = result["matched_sd_id"]
                            trial_sd = current_sd

                            if current_sd is not None:
                                print(f"current_sd={current_sd}")
                                print(f"completed_sds={completed_sds}")
                                if current_sd in completed_sds:

                                    text = f"You have already completed {current_sd} please move onto a different SD."

                                    await self.speak_text(expr=expr, text=text)

                                    agent.state.latest_transcript = None
                                    current_sd = None
                                    trial_sd = None
                                    continue
                            
                            print(f"[SD DETECTED] {current_sd}")

                            feedback.reset()

                            self.log_transcript(
                                feedback=feedback,
                                trial_state=trial_state,
                                transcript=transcript,
                                recognized_as=current_sd,
                                successful=(current_sd is not None),
                            )

                            if current_sd is not None:

                                feedback.trial_id = current_sd
                                feedback.expected_sd = trial_data[current_sd]["sd"]
                                feedback.correctness = trial_data[current_sd]["correctness"]

                                state = CurrentState.KID
                                trial_state = TrialState.KID_BEHAVIOR_1

                                print(f"Trial SD: {trial_sd}")
                                print(f"Current SD: {current_sd}")

                            else:
                                await self.flash_red_led(expr)

                        await asyncio.sleep(0.1)

                    elif trial_state == TrialState.REINFORCEMENT:
                        
                        transcript = agent.state.latest_transcript

                        print("REINFORCEMENT STARTED")

                        if transcript is not None:
                            reset_inactivity_timer()

                            self.log_transcript(
                                feedback=feedback,
                                trial_state=trial_state,
                                transcript=transcript,
                                recognized_as=current_sd,
                                successful=(current_sd is not None),
                            )

                            print(f"Trial SD: {trial_sd}")
                            print(f"Current SD: {current_sd}")


                            print(f"Reinforcement_Source: {reinforcement_source}")

                            if reinforcement_source == "prompting":

                                state = CurrentState.USER
                                trial_state = TrialState.HP_SD
                                agent.state.latest_transcript = None
                                reinforcement_source = None
                                reset_inactivity_timer()
                               
                                

                            elif reinforcement_source == "hp_sds":

                                state = CurrentState.USER
                                trial_state = TrialState.RETRY_SD
                                agent.state.latest_transcript = None
                                reinforcement_source = None
                                reset_inactivity_timer()

                            elif reinforcement_source in ["correct", "retry"]:

                                state = CurrentState.TRAINER
                                trial_state = TrialState.FEEDBACK
                                agent.state.latest_transcript = None
                                reinforcement_source = None
                                reset_inactivity_timer()
                            await self.turn_off_green_led(expr=expr)
                            trial = trial_data[trial_sd]

                            await self.run_kid_behavior(
                                expr,
                                trial["reinforce_behavior"]
                            )

                            current_sd = None


                        await asyncio.sleep(0.1)

                    elif trial_state == TrialState.PROMPTING:
                        await self.turn_on_green_led(expr=expr)

                        result = await self.handle_sd_recognition(
                            transcript=agent.state.latest_transcript,
                            emotion=agent.state.latest_emotion,
                            recognizer=sd_recognizer,
                            feedback=feedback,
                            trial_state=trial_state,
                            expected_sd=trial_sd,
                            next_trial_state=TrialState.KID_BEHAVIOR_2,
                            state=state,
                            last_processed=last_processed,
                        )

                        if result:
                            reset_inactivity_timer()

                            last_processed = result["last_processed"]
                            current_sd = result["current_sd"]

                            if result["success"]:

                                state = result["next_state"]
                                trial_state = result["next_trial_state"]

                            else:
                                await self.flash_red_led(expr)

                        await asyncio.sleep(0.1)

                    elif trial_state == TrialState.HP_SD:
                        await self.turn_on_green_led(expr=expr)

                        result = await self.handle_sd_recognition(
                            transcript=agent.state.latest_transcript,
                            emotion=agent.state.latest_emotion,
                            recognizer=hp_recognizer,              
                            feedback=feedback,
                            trial_state=trial_state,
                            expected_sd=None,                     
                            next_trial_state=TrialState.KID_BEHAVIOR_HP,
                            state=state,
                            last_processed=last_processed,
                        )

                        if result:
                            reset_inactivity_timer()

                            last_processed = result["last_processed"]
                            current_sd = result["current_sd"]

                            if result["success"]:

                                state = result["next_state"]
                                trial_state = result["next_trial_state"]

                            else:
                                await self.flash_red_led(expr)

                        await asyncio.sleep(0.1)

                    elif trial_state == TrialState.RETRY_SD:
                        await self.turn_on_green_led(expr=expr)

                        result = await self.handle_sd_recognition(
                            transcript=agent.state.latest_transcript,
                            emotion=agent.state.latest_emotion,
                            recognizer=sd_recognizer,
                            feedback=feedback,
                            trial_state=trial_state,
                            expected_sd=trial_sd,                  # Must match original SD
                            next_trial_state=TrialState.KID_BEHAVIOR_RETRY,
                            state=state,
                            last_processed=last_processed,
                        )

                        if result:
                            reset_inactivity_timer()

                            last_processed = result["last_processed"]
                            current_sd = result["current_sd"]

                            if result["success"]:

                                state = result["next_state"]
                                trial_state = result["next_trial_state"]

                            else:
                                await self.flash_red_led(expr)

                        await asyncio.sleep(0.1)
                # -------------------------
                # KID STATE
                # -------------------------
                elif state == CurrentState.KID:

                    if trial_state == TrialState.KID_BEHAVIOR_1:

                        await self.turn_off_green_led(expr=expr)
                        trial = trial_data[current_sd]

                        await self.run_kid_behavior(
                            expr,
                            trial["child_behavior"]
                        )

                        state = CurrentState.USER
                        agent.state.latest_transcript = None
                        if trial["correctness"] == "Correct":
                            reinforcement_source = "correct"
                            trial_state = TrialState.REINFORCEMENT
                            agent.state.latest_transcript = None

                        elif trial["correctness"] == "No Response":
                            trial_state = TrialState.PROMPTING
                            reset_inactivity_timer()

                        await self.turn_on_green_led(expr=expr)

                        await asyncio.sleep(0.1)

                    elif trial_state == TrialState.KID_BEHAVIOR_2:
                        await self.turn_off_green_led(expr=expr)

                        trial = trial_data[current_sd]

                        await self.run_kid_behavior(
                            expr,
                            trial["prompted_behavior"]
                        )

                        reinforcement_source = "prompting"

                        state = CurrentState.USER
                        trial_state = TrialState.REINFORCEMENT
                        agent.state.latest_transcript = None

                        await self.turn_on_green_led(expr=expr)
                        await asyncio.sleep(0.1)

                    elif trial_state == TrialState.KID_BEHAVIOR_HP:
                        await self.turn_off_green_led(expr=expr)

                        hp_trial = hp_trial_data[current_sd]

                        await self.run_kid_behavior(
                            expr,
                            hp_trial["child_behavior"]
                        )

                        current_sd = None
                        reinforcement_source = "hp_sds"

                        state = CurrentState.USER
                        trial_state = TrialState.REINFORCEMENT
                        agent.state.latest_transcript = None

                        await self.turn_on_green_led(expr=expr)
                        await asyncio.sleep(0.1)

                    elif trial_state == TrialState.KID_BEHAVIOR_RETRY:
                        await self.turn_off_green_led(expr=expr)

                        trial = trial_data[current_sd]

                        await self.run_kid_behavior(
                            expr,
                            trial["retry_behavior"]
                        )

                        reinforcement_source = "retry"
                        agent.state.latest_transcript = None

                        state = CurrentState.USER
                        trial_state = TrialState.REINFORCEMENT
                        agent.state.latest_transcript = None

                        await self.turn_on_green_led(expr=expr)
                        await asyncio.sleep(0.1)
                       

                    await asyncio.sleep(0.1)

                elif state == CurrentState.TRAINER:
                    if trial_state == TrialState.FEEDBACK:
                        await self.turn_off_green_led(expr=expr)

                        # Calculate feedback
                        turn = {
                            "embodiment": "trainer",
                            "verbal": {
                                "text": " "
                            },
                            "nonverbals": [
                                {
                                    "channel": "led",
                                    "action": "on",
                                    "color": "#FFBB00",
                                    "duration": 2.0
                                }
                            ]
                        }
                        packet = expr.build(turn)
                        await expr.execute(agent_type=self.agent, embodiment="trainer", packet=packet)

                        await asyncio.sleep(0.5)
                        evaluation_payload = feedback.build_evaluation_payload()
                        evaluation = evaluate_dtt_session(evaluation_payload)

                        print(json.dumps(evaluation, indent=2))

                        # Generate feedback text and execute it
                        feedback_text = evaluation["feedback_statement"]
                        feedback_placeholder = {
                            "embodiment": "trainer",
                            "verbal": {"text": feedback_text},
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
                        packet = expr.build(feedback_placeholder)
                        await expr.execute(agent_type=self.agent, embodiment=feedback_placeholder["embodiment"], packet=packet)

                        # Wait for reinforcement
                        sleep_time = (len(feedback_text) / 50)
                        await asyncio.sleep(sleep_time + 0.3)

                        # Reset state and trial state
                        agent.state.latest_transcript = None
                        print(f"{feedback_text}")
                        reinforcement_source = None

                        turn = {
                            "embodiment": "trainer",
                            "verbal": {
                                "text": ""
                            },
                            "nonverbals": [
                                {
                                    "channel": "led",
                                    "action": "off",
                                    "color": "#FFBB00",
                                    "duration": 2.0
                                }
                            ]
                        }
                        packet = expr.build(turn)
                        await expr.execute(agent_type=self.agent, embodiment="trainer", packet=packet)
                        agent.state.latest_transcript = None
                        await self.turn_on_green_led(expr=expr)
                        if trial_sd is not None:
                            completed_sds.add(trial_sd)

                        print(f"Completed SDs: {completed_sds}")
                        if len(completed_sds) >= 6:
                                #Play Final Thing wrapping everything up
                            final_trial = trial_data["SD_7"]    
                            self.run_kid_behavior(expr=expr, behavior=final_trial["child_behavior"])
                            DTT_IN_PROGRESS = False
                            print("You're Done")
                        else:
                            state = CurrentState.USER
                            trial_state = TrialState.SD
                    

        finally:
            perception_task.cancel()

        
       
def __main__():
    DTT.main_dtt_loop()