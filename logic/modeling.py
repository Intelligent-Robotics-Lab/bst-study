import json
import asyncio
from expression_module.expression_module import ExpressionModule

class Modeling:

    def __init__(self, agent=None):
        self.agent = agent

    async def execute(self):
        print("Executing modeling module")

        with open("data/modeling_data.json", "r") as f:
            data = json.load(f)

        steps = data["steps"]

        expr = ExpressionModule()

        for step in steps:

            packet = expr.build(step)

            await expr.execute(self.agent, step["embodiment"], packet)

            # optional pacing between teaching steps
            await asyncio.sleep(1.0)