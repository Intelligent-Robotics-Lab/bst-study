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

# =====================================================
# ADD THESE IMPORTS
# =====================================================

from dataclasses import dataclass

# =====================================================
# ADD THIS ENUM
# =====================================================

class SystemCommand(Enum):
    RESTART = "restart"
    WHERE_AM_I = "where_am_i"
    STOP = "stop"
    HELP = "help"
    NONE = "none"

# =====================================================
# ADD THIS DATACLASS
# =====================================================

@dataclass
class StateSnapshot:
    state: CurrentState
    trial_state: TrialState
    trial_sd: str | None
    current_sd: str | None

# =====================================================
# ADD THESE METHODS INSIDE DTT CLASS
# =====================================================

    # =====================================================
    # INTERRUPT / COMMAND SYSTEM
    # =====================================================

    


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
            "redo",
            "try again",
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
#################################################################################
#                           MAIN DTT LOOP                                       #
#################################################################################




    async def main_dtt_loop(self):

        state = CurrentState.USER
        trial_state = TrialState.SD 
        trial_sd = None
        current_sd = None
        reinforcement_source = None

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

        try:

            while DTT_IN_PROGRESS:
                
                # Debug print
                print(f"\n[STATE] {state} | {trial_state}")
                print(f"[TRACK] trial_sd={trial_sd} current_sd={current_sd}")
                self.current_trial_state = trial_state
                self.current_trial_sd = trial_sd
                transcript = agent.state.latest_transcript
                command = self.detect_system_command(
                    transcript
                )

                if command != SystemCommand.NONE:

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

                            last_processed = transcript

                            observed = {
                                "verbal_text": transcript,
                                "emotion": emotion
                            }

                            result = sd_recognizer.recognize(observed_input=observed)

                            current_sd = result["matched_sd_id"]
                            trial_sd = current_sd
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
                                await expr.execute(agent_type=self.agent, embodiment="kid", packet=packet)

                                await asyncio.sleep(0.5)

                        await asyncio.sleep(0.1)
                    elif trial_state == TrialState.REINFORCEMENT:

                        transcript = agent.state.latest_transcript
                        emotion = agent.state.latest_emotion
                        
                        print("REINFORCEMENT STARTED")

                        if transcript is not None:

                            self.log_transcript(
                                feedback=feedback,
                                trial_state=trial_state,
                                transcript=transcript,
                                recognized_as=current_sd,
                                successful=(current_sd is not None),
                            )

                            print(f"Trial SD: {trial_sd}")
                            print(f"Current SD: {current_sd}")

                            current_sd = None

                            # =========================================================
                            # CONTROL FLOW DECISION POINT (IMPORTANT)
                            # =========================================================
                            print(f"Reinforcement_Source: {reinforcement_source}")
                            if reinforcement_source == "prompting":
                                # THESE DO NOT TRIGGER FEEDBACK
                                state = CurrentState.USER
                                trial_state = TrialState.HP_SD
                            elif reinforcement_source == "hp_sd":
                                state = CurrentState.USER
                                trial_state = TrialState.RETRY_SD

                            elif reinforcement_source == "retry":
                                # ONLY THIS PATH TRIGGERS FEEDBACK
                                state = CurrentState.TRAINER
                                trial_state = TrialState.FEEDBACK

                            reinforcement_source = None

                        await asyncio.sleep(0.1)


                    elif trial_state == TrialState.PROMPTING:
                        current_sd = None
                        transcript = agent.state.latest_transcript
                        emotion = agent.state.latest_emotion

                        if transcript and transcript != last_processed:

                            last_processed = transcript

                            observed = {
                                "verbal_text": transcript,
                                "emotion": emotion
                            }

                            result = sd_recognizer.recognize(observed_input=observed)

                            current_sd = result["matched_sd_id"]

                            print(f"[PROMPTING DETECTED] {current_sd}")
                            self.log_transcript(
                                feedback=feedback,
                                trial_state=trial_state,
                                transcript=transcript,
                                recognized_as=current_sd,
                                successful=(
                                    current_sd == trial_sd
                                ),
                            )
                            if current_sd is not None and current_sd == trial_sd:

                                state = CurrentState.KID
                                trial_state = TrialState.KID_BEHAVIOR_2
                                print(f"Trial SD: {trial_sd}")
                                print(f"Current SD: {current_sd}")
                            else:
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
                                await expr.execute(agent_type=self.agent, embodiment="kid", packet=packet)

                                await asyncio.sleep(0.5)
                        await asyncio.sleep(0.1)
                       
                    elif trial_state == TrialState.HP_SD:
                        current_sd = None
                        transcript = agent.state.latest_transcript
                        emotion = agent.state.latest_emotion

                        if transcript and transcript != last_processed:

                            last_processed = transcript

                            observed = {
                                "verbal_text": transcript,
                                "emotion": emotion
                            }

                            result = hp_recognizer.recognize(observed_input=observed)

                            current_sd = result["matched_sd_id"]

                            print(f"[HP_SD DETECTED] {current_sd}")
                            self.log_transcript(
                                feedback=feedback,
                                trial_state=trial_state,
                                transcript=transcript,
                                recognized_as=current_sd,
                                successful=(current_sd is not None),
                            )
                            if current_sd is not None:

                                state = CurrentState.KID
                                trial_state = TrialState.KID_BEHAVIOR_HP
                                print(f"Trial SD: {trial_sd}")
                                print(f"Current SD: {current_sd}")
                            else:
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
                                await expr.execute(agent_type=self.agent, embodiment="kid", packet=packet)

                                await asyncio.sleep(0.5)

                        await asyncio.sleep(0.1)
                    elif trial_state == TrialState.RETRY_SD:
                        current_sd = None
                        transcript = agent.state.latest_transcript
                        emotion = agent.state.latest_emotion

                        if transcript and transcript != last_processed:

                            last_processed = transcript

                            observed = {
                                "verbal_text": transcript,
                                "emotion": emotion
                            }

                            result = sd_recognizer.recognize(observed_input=observed)

                            current_sd = result["matched_sd_id"]
                            
                            self.log_transcript(
                                feedback=feedback,
                                trial_state=trial_state,
                                transcript=transcript,
                                recognized_as=current_sd,
                                successful=(
                                    current_sd == trial_sd
                                ),
                            )

                            print(f"[RETRY SD DETECTED] {current_sd}")
                            if current_sd is not None and current_sd == trial_sd:
                                
                                state = CurrentState.KID
                                trial_state = TrialState.KID_BEHAVIOR_RETRY
                                print(f"Trial SD: {trial_sd}")
                                print(f"Current SD: {current_sd}")
                            else:
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
                                await expr.execute(agent_type=self.agent, embodiment="kid", packet=packet)

                                await asyncio.sleep(0.5)
                        await asyncio.sleep(0.1)


                # -------------------------
                # KID STATE
                # -------------------------
                elif state == CurrentState.KID:

                    if trial_state == TrialState.KID_BEHAVIOR_1:

                        trial = trial_data[current_sd]

                        print(f"[KID PHASE] Executing {current_sd}")

                        packet = expr.build(trial["child_behavior"])

                        await expr.execute(
                            self.agent,
                            trial["child_behavior"]["embodiment"],
                            packet
                        )

                        sleep_time = (len(trial["child_behavior"]["verbal"]["text"]) / 14) * 1.15

                        # wait for reinforcement
                        await asyncio.sleep(sleep_time + 0.3)

                        # reset + return to USER
                        agent.state.latest_transcript = None
                        state = CurrentState.USER
                       
                        if trial["correctness"] == "Correct":
                            trial_state = TrialState.REINFORCEMENT
                        elif trial["correctness"] == "No Response":
                            trial_state = TrialState.PROMPTING

                        await asyncio.sleep(0.1)
                    if trial_state == TrialState.KID_BEHAVIOR_2:

                        trial = trial_data[current_sd]

                        print(f"[KID PHASE] Executing {current_sd}")

                        packet = expr.build(trial["prompted_behavior"])

                        await expr.execute(
                            self.agent,
                            trial["prompted_behavior"]["embodiment"],
                            packet
                        )

                        sleep_time = (len(trial["prompted_behavior"]["verbal"]["text"]) / 14) * 1.15

                        # wait for reinforcement
                        await asyncio.sleep(sleep_time + 0.3)

                        # reset + return to USER
                        agent.state.latest_transcript = None
                        reinforcement_source = "propmting"

                        state = CurrentState.USER
                        trial_state = TrialState.REINFORCEMENT
                       
                        print(f"Trial SD: {trial_sd}")
                        print(f"Current SD: {current_sd}")

                        await asyncio.sleep(0.1)
                    if trial_state == TrialState.KID_BEHAVIOR_HP:

                        hp_trial = hp_trial_data[current_sd]

                        print(f"[KID PHASE] Executing {current_sd}")

                        packet = expr.build(hp_trial["child_behavior"])

                        await expr.execute(
                            self.agent,
                            hp_trial["child_behavior"]["embodiment"],
                            packet
                        )
                        sleep_time = (len(hp_trial["child_behavior"]["verbal"]["text"]) / 14) * 1.15

                        # wait for reinforcement
                        await asyncio.sleep(sleep_time + 0.3)

                        # reset + return to USER
                        agent.state.latest_transcript = None
                        current_sd = None
                        reinforcement_source = "hp_sds"
                        
                        state = CurrentState.USER
                        trial_state = TrialState.REINFORCEMENT
                        
                        print(f"Trial SD: {trial_sd}")
                        print(f"Current SD: {current_sd}")

                        await asyncio.sleep(0.1)
                    if trial_state == TrialState.KID_BEHAVIOR_RETRY:

                        trial = trial_data[current_sd]

                        print(f"[KID PHASE] Executing {current_sd}")

                        packet = expr.build(trial["retry_behavior"])

                        await expr.execute(
                            self.agent,
                            trial["retry_behavior"]["embodiment"],
                            packet
                        )

                        sleep_time = (len(trial["retry_behavior"]["verbal"]["text"]) / 14) * 1.15

                        # wait for reinforcement
                        await asyncio.sleep(sleep_time + 0.3)

                        # reset + return to USER
                        agent.state.latest_transcript = None
                        reinforcement_source = "retry"
                        state = CurrentState.USER
                        trial_state = TrialState.REINFORCEMENT
                       
                        await asyncio.sleep(0.1)

                elif state == CurrentState.TRAINER:
                    if trial_state == TrialState.FEEDBACK:
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
                                    "color": "#00FF00",
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
                        sleep_time = (len(feedback_text) / 21)
                        await asyncio.sleep(sleep_time + 0.3)

                        # Reset state and trial state
                        agent.state.latest_transcript = None
                        print(f"{feedback_text}")
                        reinforcement_source = None

                        state = CurrentState.USER
                        trial_state = TrialState.SD
                    

        finally:
            perception_task.cancel()

            









       
def __main__():
    DTT.main_dtt_loop()