import asyncio
from logic.instruction import Instruction
from logic.modeling import Modeling
from logic.dtt import DTT
from logic.tutorial import Tutorial
import agent_layer.Furhat.Lib.furhat_manager as FurhatManager
import agent_layer.Unreal.Lib.unreal_manager as UnrealManager

AGENT_TYPE = "Unreal"

_furhats = None

async def BST():

    global _furhats

    study_config = {
        "participant_name": input("Participant name: "),
        "configuration": input("Configuration (1, 2, or 3): "),
        "trainer_feedback_style": input("Feedback style (supportive or neutral): ")
    }

    input("\nPress ENTER to start BST...")

    if AGENT_TYPE == "Furhat":
        _furhats = await FurhatManager.initialize_furhat()
        print("[CONNECTED TO FURHAT]")
    if AGENT_TYPE == "Unreal":
        await UnrealManager.initialize_unreal()


    try:
        await Tutorial(agent=AGENT_TYPE, study_config=study_config).execute()
        print("Executed tutorial")

        await Instruction(agent=AGENT_TYPE, study_config=study_config).execute()
        print("Executed instruction")

        await Modeling(agent=AGENT_TYPE, study_config=study_config).execute()
        print("Executed modeling")

        await DTT(agent=AGENT_TYPE, study_config=study_config).execute()
        print("Executed DTT")

    finally:
        if AGENT_TYPE == "Furhat":
            await FurhatManager.shutdown_furhats()
            print("[PIPELINE COMPLETE - FURHAT READY]")