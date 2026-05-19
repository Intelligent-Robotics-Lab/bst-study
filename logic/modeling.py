import json
import asyncio
from expression_module.expression_module import ExpressionModule


class Modeling:

    def __init__(self, agent=None):
        self.agent = agent

    async def wait_for_input(self, prompt="> "):
        return await asyncio.to_thread(input, prompt)

    async def execute(self):

        print("Executing modeling module")

        with open("data/modeling_data.json", "r") as f:
            steps = json.load(f)["steps"]

        expr = ExpressionModule()
        current_index = 0

        while current_index < len(steps):

            step = steps[current_index]

            if step.get("type") == "checkpoint":

                action = await self.handle_checkpoint(step)

                if action == "repeat":

                    section = step["section"]
                    current_index = self.find_section_start(steps, section)
                    continue

                current_index += 1
                continue

            packet = expr.build(step)

            await expr.execute(
                self.agent,
                step["embodiment"],
                packet
            )

            current_index += 1

        print("\nMODELING COMPLETE")

    async def handle_checkpoint(self, step):

        section = step["section"]

        print(f"\n[CHECKPOINT: {section}]")
        print("1. Continue")
        print("2. Repeat section")
        print("3. Clarify")

        choice = await self.wait_for_input("> ")

        if choice == "1":
            return "continue"

        elif choice == "2":
            return "repeat"

        elif choice == "3":
            print(f"\nClarifying {section}...")
            await asyncio.sleep(1)
            print("Key idea: observe SD → response → reinforcement pattern")
            return await self.handle_checkpoint(step)

        return "continue"

    def find_section_start(self, steps, section):

        for i, step in enumerate(steps):
            if step.get("section") == section:
                return i

        return 0