import json
import asyncio
from expression_module.expression_module import ExpressionModule
from logic.feedback import Feedback
from logic.feedback import evaluate_dtt_session
from logic.sd_recognizer import SDRecognizer

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

    async def execute(self):
        await self.main_dtt_loop()

    async def main_dtt_loop(self):

        expr = ExpressionModule()
        feedback = Feedback(self.agent)

        with open("data/trial_data.json", "r") as f:
            trial_data = json.load(f)["trial_data"]

        recognizer = SDRecognizer(trial_data)

        # Observed will be defined by the Perception Layer
        observed = {
            "verbal_text": "I want stickers!",
            "nonverbals": {
                "face": "happy",
                "head": "nod"
            }
        }

        result = recognizer.recognize(observed)

        print(result["matched_sd_id"])
        print(result["confidence"])

        current_sd_id = 1
        max_id = 6

        while current_sd_id <= max_id:

            await self.wait_for_sd()

            trial = trial_data[f"SD_{current_sd_id}"]
            correctness = trial["correctness"]

            print(f"\n[SD {current_sd_id}] Correctness: {correctness}")

            packet = expr.build(trial["child_behavior"])

            await expr.execute(
                self.agent,
                trial["child_behavior"]["embodiment"],
                packet
            )

            if correctness == "Correct":

                await self.wait_for_reinforcement()

                fb_packet = feedback.build("Correct", phase="reinforcement")

                packet = expr.build(fb_packet)

                await expr.execute(
                    self.agent,
                    fb_packet["embodiment"],
                    packet
                )


            elif correctness == "No Response":

                await self.wait_for_prompt()
                await self.hp_sd_protocol()

                fb_packet = feedback.build("No Response", phase="prompt")

                packet = expr.build(fb_packet)

                await expr.execute(
                    self.agent,
                    fb_packet["embodiment"],
                    packet
                )


            elif correctness == "Incorrect":

                await self.wait_for_input("Press ENTER for error correction ")
                await self.hp_sd_protocol()

                fb_packet = feedback.build("Incorrect", phase="correction")

                packet = expr.build(fb_packet)

                await expr.execute(
                    self.agent,
                    fb_packet["embodiment"],
                    packet
                )

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
            hp_data = json.load(f)["trial_data"]

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