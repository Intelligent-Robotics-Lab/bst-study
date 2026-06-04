from furhat_realtime_api import AsyncFurhatClient
import asyncio

import requests
import wave
from pydub import AudioSegment

async def main():

    furhat = AsyncFurhatClient("141.210.88.202")
    await furhat.connect()
    print("Connected to Furhat")
    await furhat.request_system_config(volume=30)
    try:

        await furhat.request_speak_audio(url="http://141.210.88.244:8000/furhat.wav")
    except Exception as e:
        print("ERROR:", repr(e))
    await asyncio.sleep(3)

    await asyncio.sleep(3)
    # await furhat.request_speak_text("That ...is... INTERESTING.")
    # await asyncio.sleep(2)

    # await furhat.request_speak_text("That is interesting.")

    # await asyncio.gather(demo(furhat))
    
    

    print("Done")
    await furhat.disconnect()

asyncio.run(main())