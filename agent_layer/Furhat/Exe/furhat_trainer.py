import asyncio
import expression_module.expression_instruction as expression_instruction
import agent_layer.Furhat.Lib.furhat_trainer_behavior_library as trainer_library
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior

"""This class is responsible for executing the behavior of the trainer based upon the text and nonverbals passed from the expression module. 
It uses the furhat_trainer_behavior_library to execute the speak and gesture behaviors of the trainer."""
class FurhatTrainer:
    def __init__(self, furhat, text, nonverbals):
        self.furhat = furhat
        self.text = text
        self.nonverbals = nonverbals

    async def execute(self):
        asyncio.gather(
            trainer_library.speak(furhat=self.furhat, message=self.text),
            trainer_library.gesture(furhat=self.furhat, nonverbals=self.nonverbals)
        )
