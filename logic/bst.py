import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior
from logic.instruction import Instruction
# from modeling import Modeling
# from dtt import DTT

FURHAT_TRAINER_IP = "141.210.88.11"

async def BST():
    await Instruction().execute()
    print("Executed instruction")
    # Modeling
    # DTT

