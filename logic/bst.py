import asyncio
from logic.instruction import Instruction
from logic.modeling import Modeling
from logic.dtt import DTT
from logic.tutorial import Tutorial
import agent_layer.Furhat.Lib.furhat_manager as FurhatManager
from logic.sync_client import SyncClient
from logic.launch_client import LaunchClient

AGENT_TYPE = "Furhat"
PLATFORM_BASE = "http://141.210.88.210:8080"

_furhats = None

async def BST():

    global _furhats

    session_id = input("Session_id (from the console): ")
    participant_name = input("Participant name: ")
    launch = LaunchClient(session_id, PLATFORM_BASE)

    cfg = await launch.get_config()
    await launch.ack("config_received")

    study_config = {
        "session_id": cfg["session_id"],
        "configuration": cfg["pb_order_group"],
        "trainer_feedback_style": cfg["support_label"],
        "platform_base": cfg["platform_base"],
        "participant_name": participant_name
    }

    await launch.wait_for_start()

    sync = SyncClient(study_config["session_id"], study_config["platform_base"])
    await sync.register(pb_order_group=int(study_config["configuration"]), 
        support_condition=1 if study_config["trainer_feedback_style"] == "supportive" else 0) # Confirm pb_order_group / support_condition alignment

    # Verify the object
    print(f"BST] sync id = {id(sync)}")

    if AGENT_TYPE == "Furhat":
        _furhats = await FurhatManager.initialize_furhat()
        print("[CONNECTED TO FURHAT]")

    try:
        await launch.ack("started")

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