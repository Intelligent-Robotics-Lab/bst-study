import asyncio
from logic.instruction import Instruction
from logic.modeling import Modeling
from logic.dtt import DTT
from logic.tutorial import Tutorial
import agent_layer.Furhat.Lib.furhat_manager as FurhatManager

AGENT_TYPE = "Furhat"

_furhats = None

async def BST():

    global _furhats

    if AGENT_TYPE == "Furhat":
        _furhats = await FurhatManager.initialize_furhat()
        print("[CONNECTED TO FURHAT]")

    #await Tutorial(agent=AGENT_TYPE).execute()
    print("Executed tutorial")

    #await Instruction(agent=AGENT_TYPE).execute()
    print("Executed instruction")

    #await Modeling(agent=AGENT_TYPE).execute()
    print("Executed modeling")

    await DTT(agent=AGENT_TYPE).execute()
    print("Executed DTT")

    # Should probably add some kind of conclusionary statements

    if AGENT_TYPE == "Furhat":
        await FurhatManager.shutdown_furhats()
        print("[PIPELINE COMPLETE - FURHAT READY]")