import asyncio
import agent_layer.Furhat.furhat_trainer_behavior_library as furhat_trainer

class ExpressionInstruction:
    def __init__(self, agent):
        self.agent = agent

    async def execute(self):
        print("Executing expression instruction")
        self.instruction_text = "This is how you do DTT for BST"
        await furhat_trainer.speak(furhat=self.agent, text=self.instruction_text)
