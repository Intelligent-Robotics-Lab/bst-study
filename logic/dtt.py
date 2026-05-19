import json
import asyncio
from expression_module.expression_module import ExpressionModule
from logic.feedback import Feedback


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