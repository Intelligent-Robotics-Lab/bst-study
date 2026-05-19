import json
import asyncio
from expression_module.expression_module import ExpressionModule

"""This class contains the logic to complete the instruction phase of BST"""
class Instruction:

    def __init__(self, agent=None):
        self.agent = agent

    """Current implementation relies on stepping through one step after the other, will be updated to have some interaction flow."""
    async def execute(self):
        print("Executing instruction module")

        with open("data/instruction_data.json", "r") as f:
            data = json.load(f)

        steps = data["steps"]

        # Create expression module once
        expr = ExpressionModule()

        for step in steps:

            packet = expr.build(step)
            #From Perception check to see if user wants to repeat the last step for clarity if the ASR ever picks up user audio that says to stop or repeat or something similar have it replay the current step in the insturction phase
            await expr.execute(agent_type=self.agent, embodiment=step["embodiment"],packet=packet)

            # optional pacing between teaching steps
            await asyncio.sleep(1.0)