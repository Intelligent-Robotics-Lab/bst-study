
import json
import asyncio
from expression_module.expression_module import ExpressionModule


class DTT:

    def __init__(self, agent=None):
        self.agent = agent

    async def wait_for_input(self, prompt="> "):
        return await asyncio.to_thread(input, prompt)

    async def wait_for_sd(self):
        print("\n[WAITING FOR SD]")
        await self.wait_for_input("Press ENTER when SD is delivered ")

    async def wait_for_reinforcement(self):
        print("\n[WAITING FOR REINFORCEMENT]")
        await self.wait_for_input("Press ENTER when reinforcement is delivered ")

    async def wait_for_prompt(self):
        print("\n[WAITING FOR PROMPT]")
        await self.wait_for_input("Press ENTER when prompt is delivered ")

    async def execute(self):
        await self.main_dtt_loop()

    async def main_dtt_loop(self):
        expr = ExpressionModule()

        with open("data/trial_data.json", "r") as f:
            trial_data = json.load(f)

        trial_data = trial_data["trial_data"]
        current_sd_id = 1
        max_id = 6

        while current_sd_id < max_id:

            await self.wait_for_sd()

            current_trial = trial_data[f"SD_{current_sd_id}"]

            correctness = current_trial["correctness"]

            print(f"\nCurrent Trial Correctness: {correctness}")

            # Child behavior
            packet = expr.build(current_trial["child_behavior"])

            await expr.execute(
                agent_type=self.agent,
                embodiment=current_trial["child_behavior"]["embodiment"],
                packet=packet
            )

            # CORRECT RESPONSE
            if correctness == "Correct":

                await self.wait_for_reinforcement()

            # NO RESPONSE
            elif correctness == "No Response":

                await self.wait_for_prompt()

                print("Child receives prompt...")

                await asyncio.sleep(1)

                print("Running High Probability SD protocol...")

                await asyncio.sleep(1)

                print("Child gives correct answer")

                await self.wait_for_reinforcement()

            # INCORRECT RESPONSE
            elif correctness == "Incorrect":

                print("Waiting for error correction...")

                await self.wait_for_input(
                    "Press ENTER when error correction occurs "
                )

                print("Child acknowledges correction")

                await asyncio.sleep(1)

                print("Running High Probability SD protocol...")

                await asyncio.sleep(1)

                print("Child gives correct answer")

                await self.wait_for_reinforcement()

            current_sd_id += 1

        print("\nDTT SESSION COMPLETE")

    async def hp_sd_protocol(self):
        expr = ExpressionModule()


        with open("data/hp_trial_data.json", "r") as f:
            hp_data = json.load(f)
        hp_data = hp_data["trial_data"]


        correctness = hp_data["correctness"]

        print(f"\nCurrent Trial Correctness: {correctness}")

        # Child behavior
        packet = expr.build(hp_data["child_behavior"])

        await expr.execute(
                agent_type=self.agent,
                embodiment=hp_data["child_behavior"]["embodiment"],
                packet=packet
            )

        # CORRECT RESPONSE
        if correctness == "Correct":

            await self.wait_for_reinforcement()
        