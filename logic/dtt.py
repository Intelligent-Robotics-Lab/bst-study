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

    async def main_dtt_loop(self):

        state = CurrentState.USER
        trial_state = TrialState.SD 
        current_sd = None
        with open("data/trial_data.json", "r") as f:
            trial_data = json.load(f)["trial_data"]

        with open("data/hp_trial_data.json", "r") as f:
            hp_trial_data = json.load(f)
        
        expr = ExpressionModule()
        sd_recognizer = SDRecognizer(trial_data=trial_data)
        hp_recognizer = SDRecognizer(trial_data=hp_trial_data)
        agent = SampleInteractionAgent(silence_timeout=1.0)

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

                # -------------------------
                # USER STATE
                # -------------------------
                if state == CurrentState.USER:
                    if trial_state == TrialState.SD:
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

                            print(f"[SD DETECTED] {current_sd}")

                        if current_sd is not None:
                            state = CurrentState.KID
                            trial_state = TrialState.KID_BEHAVIOR_1

                        await asyncio.sleep(0.1)
                    elif trial_state == TrialState.REINFORCEMENT:
                        transcript = agent.state.latest_transcript
                        emotion = agent.state.latest_emotion
                        if transcript != None: # Update to be if response is incorrect we don't get feedback
                            state = CurrentState.TRAINER
                            trial_state = TrialState.FEEDBACK
                        await asyncio.sleep(0.1)


                    elif trial_state == TrialState.PROMPTING: # Needs to match the same SD as the first
                        transcript = agent.state.latest_transcript
                        emotion = agent.state.latest_emotion
                        if transcript != None:
                            state = CurrentState.KID
                            trial_state = TrialState.KID_BEHAVIOR_2
                        await asyncio.sleep(0.1)
                       
                    elif trial_state == TrialState.HP_SD: # Once a HP SD is detected exhibit the kid reponse
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

                            print(f"[SD DETECTED] {current_sd}")

                            state = CurrentState.KID
                            trial_state = TrialState.KID_BEHAVIOR_HP
                        await asyncio.sleep(0.1)
                    elif trial_state == TrialState.RETRY_SD: # Must match back to the original SD and display the correct behavior
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

                            print(f"[SD DETECTED] {current_sd}")

                            state = CurrentState.KID
                            trial_state = TrialState.KID_BEHAVIOR_RETRY
                        await asyncio.sleep(0.1)

                # Missing a final reinforcement into feedback here

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

                        # wait for reinforcement
                        await asyncio.sleep(1)

                        # reset + return to USER
                        agent.state.latest_transcript = None
                        current_sd = None
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

                        # wait for reinforcement
                        await asyncio.sleep(1)

                        # reset + return to USER
                        agent.state.latest_transcript = None
                        current_sd = None
                        state = CurrentState.USER
                        trial_state = TrialState.HP_SD

                        await asyncio.sleep(0.1)
                    if trial_state == TrialState.KID_BEHAVIOR_HP:

                        trial = hp_trial_data[current_sd]

                        print(f"[KID PHASE] Executing {current_sd}")

                        packet = expr.build(trial["prompted_behavior"]) # Double check this, I think it is hp_trial_data

                        await expr.execute(
                            self.agent,
                            trial["child_behavior"]["embodiment"],
                            packet
                        )

                        # wait for reinforcement
                        await asyncio.sleep(1)

                        # reset + return to USER
                        agent.state.latest_transcript = None
                        current_sd = None
                        state = CurrentState.USER
                        trial_state = TrialState.RETRY_SD

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

                        # wait for reinforcement
                        await asyncio.sleep(1)

                        # reset + return to USER
                        agent.state.latest_transcript = None
                        current_sd = None
                        state = CurrentState.USER
                        trial_state = TrialState.REINFORCEMENT

                        await asyncio.sleep(0.1)

                elif state == CurrentState.TRAINER:
                    if trial_state == TrialState.FEEDBACK:
                        self.get_feedback_placeholder("Correct")
                        state = CurrentState.USER
                        trial_state = TrialState.SD


        finally:
            perception_task.cancel()

def __main__():
    DTT.main_dtt_loop()