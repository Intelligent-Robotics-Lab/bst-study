import asyncio
from expression_module.expression_instruction import ExpressionModuleInstruction

class Instruction:
    def __init__(self):
        pass

    async def execute(self):
        print("Executing instruction")
        await ExpressionModuleInstruction("Hello, welcome to the instruction module!", "Nod").execute()