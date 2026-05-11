import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior
from logic.instruction import Instruction
# from modeling import Modeling
# from dtt import DTT

async def BST():
    await Instruction().execute()
    # Modeling
    # DTT(Feedback)