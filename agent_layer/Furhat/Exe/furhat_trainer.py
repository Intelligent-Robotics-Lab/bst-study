import asyncio
import expression_module.expression_module as expression_module
import agent_layer.Furhat.Lib.furhat_trainer_behavior_library as trainer_library
import agent_layer.Furhat.Lib.furhat_behavior_components as copmonent

TRAINER_IP = "141.210.88.11"

"""This class is responsible for executing the behavior of the trainer based upon the text and nonverbals passed from the expression module. 
It uses the furhat_trainer_behavior_library to execute the speak and gesture behaviors of the trainer."""
class FurhatTrainer:
    def __init__(self, furhat, text, nonverbals):
        self.furhat = furhat
        self.text = text
        self.nonverbals = nonverbals

    async def execute(self, behavior):
        furhat = copmonent.connect_furhat(TRAINER_IP)

        asyncio.gather(
            trainer_library.speak(furhat=self.furhat, message=behavior.verbal.text),
            trainer_library.gesture(furhat=self.furhat, nonverbals=self.nonverbals)
        )





