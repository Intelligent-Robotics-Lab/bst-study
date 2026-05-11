import asyncio
import expression_module.expression_instruction as expression_instruction
import agent_layer.Furhat.Lib.furhat_kid_behavior_library as kid_library
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior

"""This class is responsible for executing the behavior of the kid based upon the text and nonverbals passed from the expression module. 
It uses the furhat_kid_behavior_library to execute the speak and gesture behaviors of the kid."""
class FurhatTrainer:
    def __init__(self, furhat, text, nonverbals):
        self.furhat = furhat
        self.text = text
        self.nonverbals = nonverbals

    async def execute(self):
        asyncio.gather(
            behavior.speak_text(furhat=self.furhat, message=self.text),
            behavior.start_gesture(furhat=self.furhat, gesture=self.nonverbals, intensity=3, duration=1, number_repeat=3)
        )