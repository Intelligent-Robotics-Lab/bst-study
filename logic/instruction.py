import json
import asyncio
from expression_module.expression_module import ExpressionModule


class Instruction:

    def __init__(self, agent=None):
        self.agent = agent

    async def wait_for_input(self, prompt="> "):
        return await asyncio.to_thread(input, prompt)

    async def execute(self):

        print("Executing instruction module")

        with open("data/instruction_data.json", "r") as f:
            steps = json.load(f)["steps"]

        expr = ExpressionModule()
        current_index = 0

        while current_index < len(steps):

            step = steps[current_index]

            # Checkpoint handling
            if step.get("type") == "checkpoint":

                action = await self.handle_checkpoint(step)

                if action == "repeat":
                    section = step["section"]
                    current_index = self.find_section_start(steps, section)
                    continue

                current_index += 1
                continue
            
            # Normal behavior steps
            packet = expr.build(step)

            embodiment = step.get("embodiment")
            if not embodiment:
                current_index += 1
                continue

            await expr.execute(agent_type=self.agent, embodiment=embodiment, packet=packet)

            # Small pacing buffer implemented in (could remove if desired)
            await asyncio.sleep(0.5)

            current_index += 1

        print("\nINSTRUCTION COMPLETE")

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

        # Clarification section unlikely to be included but could include LLM prompt about section or similar
        elif choice == "3":
            print(f"\nClarifying {section}...")
            await asyncio.sleep(1)
            print("Key idea: structured instruction delivery with comprehension checks")
            return await self.handle_checkpoint(step)

        return "continue"

    def find_section_start(self, steps, section):

        for i, step in enumerate(steps):
            if step.get("section") == section:
                return i

        return 0