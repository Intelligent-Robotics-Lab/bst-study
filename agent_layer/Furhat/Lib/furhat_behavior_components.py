from furhat_realtime_api import AsyncFurhatClient
import asyncio

async def connect_furhat(IP_ADDRESS):
    furhat = AsyncFurhatClient(IP_ADDRESS)
    await furhat.connect()
    print("Connected")
    return furhat


async def start_gesture(furhat, gesture, intensity, duration, number_repeat):
    #List of Gestures:
    # - BigSmile
    # - Blink
    # - BrowFrown
    # - BrowRaise
    # - CloseEyes
    # - ExpressAnger
    # - ExpressDisgust
    # - ExpressFear
    # - ExpressSad
    # - GazeAway
    # - Nod
    # - Oh
    # - OpenEyes
    # - Roll
    # - Shake
    # - Smile
    # - Suprise
    # - Thoughtful
    # - Wink
    for _ in range(number_repeat):
        await furhat.request_gesture_start(
            name=gesture, 
            intensity = intensity,
            duration= duration
        )
        await asyncio.sleep(duration)

async def speak_text(furhat, message, duration, number_repeat):
    for _ in range(number_repeat):
        await furhat.request_speak_text(message)
        await asyncio.sleep(duration)

