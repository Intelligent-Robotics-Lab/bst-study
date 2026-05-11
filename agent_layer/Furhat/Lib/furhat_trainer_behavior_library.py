import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_components as trainer

async def speak(furhat, text):
    await asyncio.gather(
        trainer.speak_text(furhat=furhat, message=text, number_repeat=1, duration=10)
    )

async def gesture(furhat, nonverbals):
    await trainer.start_gesture(furhat=furhat, gesture=nonverbals, intensity=3, duration=1, number_repeat=3)