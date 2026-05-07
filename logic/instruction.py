import asyncio
from expression_module.expression_instruction import ExpressionInstruction

class Instruction:
    def __init__(self, agent):
        self.agent = agent

    async def execute(self):
        print("Executing instruction")
        await ExpressionInstruction(agent=self.agent).execute()