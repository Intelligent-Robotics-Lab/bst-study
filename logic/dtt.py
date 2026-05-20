import json
import asyncio
from expression_module.expression_module import ExpressionModule
# from logic.feedback import Feedback
# from logic.feedback import evaluate_dtt_session
# from logic.sd_recognizer import SDRecognizer


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

    async def main_dtt_loop(self):

        expr = ExpressionModule()
        # feedback = Feedback(self.agent)

        with open("data/trial_data.json", "r") as f:
            trial_data = json.load(f)["trial_data"]

        # recognizer = SDRecognizer(trial_data)

        # Observed will be defined by the Perception Layer
        observed = {
            "verbal_text": "I want stickers!",
            "nonverbals": {
                "face": "happy",
                "head": "nod"
            }
        }

        # result = recognizer.recognize(observed)

        # print(result["matched_sd_id"])
        # print(result["confidence"])

        current_sd_id = 1
        max_id = 6

        while current_sd_id <= max_id:

            await self.wait_for_sd()

            trial = trial_data[f"SD_{current_sd_id}"]
            correctness = trial["correctness"]

            print(f"\n[SD {current_sd_id}] Correctness: {correctness}")

            packet = expr.build(trial["child_behavior"])

            await expr.execute(self.agent, trial["child_behavior"]["embodiment"], packet)

            if correctness == "Correct":

                await self.wait_for_reinforcement()

                await self.run_behavior(expr, self.get_feedback_placeholder(correctness))

            elif correctness in ["No Response", "Incorrect"]:

                await self.wait_for_prompt()

                await self.run_behavior(expr, trial["prompted_behavior"])

                await self.wait_for_reinforcement()

                await self.hp_sd_protocol()

                await self.wait_for_sd()

                await self.run_behavior(expr, trial["retry_behavior"])

                await self.wait_for_reinforcement()

                await self.run_behavior(expr, self.get_feedback_placeholder(correctness))

            current_sd_id += 1

        # This is where feedback will be called it will pass through:
        # - The Obsereved Actions of the user defined by Perception Layer
        # - The Feedback will be calculated via Ollama agent that is prompted to grade based on instruction rubic it is given
        # - Feed back will have two toggleable states one for supportive and one for non-supportive
        # - Feedback will be in textual format and then passed through as a behavior to the Agent Layer to be carried out

        print("\nDTT COMPLETE")

    async def hp_sd_protocol(self):

        expr = ExpressionModule()

        with open("data/hp_trial_data.json", "r") as f:
            hp_data = json.load(f)["hp_trial_data"]

        hp_list = list(hp_data.values())

        trial = hp_list[self.hp_index]

        print("\n[HIGH PROBABILITY SD]")

        packet = expr.build(trial["child_behavior"])

        await expr.execute(
            self.agent,
            trial["child_behavior"]["embodiment"],
            packet
        )

        if trial["correctness"] == "Correct":
            await self.wait_for_reinforcement()

        self.hp_index = (self.hp_index + 1) % len(hp_list)