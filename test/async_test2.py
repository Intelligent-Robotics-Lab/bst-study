import argparse
import asyncio
import logging
from furhat_realtime_api import AsyncFurhatClient

async def nod_head(furhat):
    for i in range(3):
        await furhat.request_gesture_start(name="Nod", intensity=1.0, duration=1.0, wait=True)
        # await asyncio.sleep(0.5)

async def shake_head(furhat):
    for i in range(3):
        await furhat.request_gesture_start(name="Shake", intensity=1.0, duration=1.0, wait=True)
        # await asyncio.sleep(0.5)

async def smile(furhat):
    await furhat.request_gesture_start(name="Smile", intensity=2.0, duration=3.0, wait=True)
    
async def thinking(furhat):
    await furhat.request_gesture_start(name="Thoughtful", intensity=2.0, duration=3.0, wait=True)

async def demo(furhat):
    await furhat.request_speak_text("Hello, I am Furhat.")

    await furhat.request_speak_text("I will nod by head."),
    await nod_head(furhat)
    await asyncio.sleep(1)

    await furhat.request_speak_text("Now I will shake my head no."),
    await shake_head(furhat)
    await asyncio.sleep(1)

    await furhat.request_speak_text("Now I will smile."),
    await smile(furhat)
    await asyncio.sleep(1)

    await furhat.request_speak_text("I am thinking."),
    await thinking(furhat)
    await asyncio.sleep(1)

    await furhat.request_speak_text("Goodbye.")

async def main():
    furhat = AsyncFurhatClient("141.210.88.11")
    await furhat.connect()
    print("Connected to Furhat")

    await furhat.request_voice_config(voice_id="Ivy-Neural (en-US) - Amazon Polly")

    await furhat.request_face_config(face_id="child - Billy")

    await asyncio.gather(demo(furhat))

    print("Done")
    await furhat.disconnect()

asyncio.run(main())