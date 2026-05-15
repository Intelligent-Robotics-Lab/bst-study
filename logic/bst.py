import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior
from logic.instruction import Instruction
from logic.modeling import Modeling
from logic.dtt import DTT
# from dtt import DTT

AGENT_TYPE = "Furhat"

async def BST():
    #await Instruction(agent=AGENT_TYPE).execute()
    #print("Executed instruction")
    #await Modeling(agent=AGENT_TYPE).execute()
    #print("Executed modeling")
    await DTT(agent=AGENT_TYPE).execute()

