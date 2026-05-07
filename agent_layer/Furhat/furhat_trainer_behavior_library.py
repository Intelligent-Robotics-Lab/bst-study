import asyncio
import agent_layer.Furhat.furhat_behavior_components as trainer

async def speak(furhat, text):
    await asyncio.gather(
        trainer.speak_text(furhat=furhat, message=text, number_repeat=1, duration=10)
    )