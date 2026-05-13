import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior
from logic.instruction import Instruction
# from modeling import Modeling
# from dtt import DTT

AGENT_TYPE = "furhat"

async def BST():
    await Instruction(agent=AGENT_TYPE).execute()
    print("Executed instruction")
    # Modeling
    # DTT

