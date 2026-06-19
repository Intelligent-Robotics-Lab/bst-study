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

    study_config = {
        "participant_name": input("Participant name: "),
        "configuration": input("Configuration (1, 2, or 3): "),
        "trainer_feedback_style": input("Feedback style (supportive or neutral): ")
    }

    input("\nPress ENTER to start BST...")

    #await Tutorial(agent=AGENT_TYPE, study_config=study_config).execute()
    #print("Executed tutorial")

    #await Instruction(agent=AGENT_TYPE, study_config=study_config).execute()
    #print("Executed instruction")

    #await Modeling(agent=AGENT_TYPE, study_config=study_config).execute()
    #print("Executed modeling")

    await DTT(agent=AGENT_TYPE, study_config=study_config).execute()
    print("Executed DTT")

    if AGENT_TYPE == "Furhat":
        await FurhatManager.shutdown_furhats()
        print("[PIPELINE COMPLETE - FURHAT READY]")