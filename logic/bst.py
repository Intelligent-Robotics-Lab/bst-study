import asyncio
import agent_layer.Furhat.furhat_behavior_components as behavior
from logic.instruction import Instruction
# from modeling import Modeling
# from dtt import DTT

async def BST():
    FURHAT_TRAINER_IP = "141.210.88.11"

    furhat_trainer = await behavior.connect_furhat(FURHAT_TRAINER_IP)

    print("BST started")

    agent = furhat_trainer

    await Instruction(agent).execute()

    agent.disconnect()