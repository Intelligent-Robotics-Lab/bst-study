import asyncio
import agent_layer.Furhat.Exe.furhat_kid as kid
import agent_layer.Furhat.Exe.furhat_trainer as trainer
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior

FURHAT_TRAINER_IP = "141.210.88.11"
# FURHAT_KID_IP = "---.---.--.--"

# Text and nonverbals are passed as the inputs to this stage and called into the agent layer
async def agent_layer(text, nonverbals, agent_type):
    if agent_type == "Furhat":  
        print("Connecting to Furhat trainer")
        furhat_trainer = await behavior.connect_furhat(FURHAT_TRAINER_IP)
        print("Connected to Furhat trainer")
        # furhat_kid = await behavior.connect_furhat(FURHAT_KID_IP)
        # print("Connected to Furhat kid")

        # Execute the behavior of the trainer based upon the text and nonverbals
        await trainer.FurhatTrainer(furhat=furhat_trainer, text=text, nonverbals=nonverbals)
        print("Executed trainer behavior")

        # await kid.FurhatKid(furhat=furhat_trainer, text=text, nonverbals=nonverbals)
        # print("Executed kid behavior")

        # Disconnect from the furhat after executing the behavior    
        furhat_trainer.disconnect()
        print("Disconnected from Furhat")

