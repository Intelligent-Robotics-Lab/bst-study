import asyncio
from logic.instruction import Instruction
from logic.modeling import Modeling
from logic.dtt import DTT
from logic.tutorial import Tutorial
import agent_layer.Furhat.Lib.furhat_manager as FurhatManager
from logic.sync_client import SyncClient

AGENT_TYPE = "Furhat"
PLATFORM_BASE = "http://141.210.88.210:8080"

_furhats = None

async def BST():

    global _furhats

    study_config = {
        "participant_name": input("Participant name: "),
        "configuration": input("Configuration (1, 2, or 3): "),
        "trainer_feedback_style": input("Feedback style (supportive or neutral): "),
        "session_id": input("Session_id (match the platform exactly): "),
        "platform_base": PLATFORM_BASE,
    }

    sync = SyncClient(study_config["session_id"], study_config["platform_base"])
    await sync.register(pb_order_group=int(study_config["configuration"]), 
        support_condition=1 if study_config["trainer_feedback_style"] == "supportive" else 0) # Confirm pb_order_group / support_condition alignment

    # Verify the object
    print(f"BST] sync id = {id(sync)}")

    if AGENT_TYPE == "Furhat":
        _furhats = await FurhatManager.initialize_furhat()
        print("[CONNECTED TO FURHAT]")

    try:
        await Tutorial(agent=AGENT_TYPE, study_config=study_config, sync=sync).execute()
        print("Executed tutorial")

        await Instruction(agent=AGENT_TYPE, study_config=study_config, sync=sync).execute()
        print("Executed instruction")

        await Modeling(agent=AGENT_TYPE, study_config=study_config, sync=sync).execute()
        print("Executed modeling")

        await DTT(agent=AGENT_TYPE, study_config=study_config, sync=sync).execute()
        print("Executed DTT")

    finally:
        await sync.complete()

        if AGENT_TYPE == "Furhat":
            await FurhatManager.shutdown_furhats()
            print("[PIPELINE COMPLETE - FURHAT READY]")