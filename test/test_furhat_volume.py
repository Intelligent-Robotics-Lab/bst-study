from furhat_realtime_api import AsyncFurhatClient
import asyncio

async def main():

    furhat = AsyncFurhatClient("141.210.88.202")
    await furhat.connect()
    print("Connected to Furhat")
    await furhat.request_system_config(volume=30)
    await furhat.request_speak_text("Hello, I am Furhat.")
    await asyncio.sleep(3)
    await furhat.request_system_config(volume=80)
    await furhat.request_speak_text("I hate you.")
    await asyncio.sleep(3)
    # await furhat.request_speak_text("That ...is... INTERESTING.")
    # await asyncio.sleep(2)

    # await furhat.request_speak_text("That is interesting.")

    # await asyncio.gather(demo(furhat))
    
    gestures = await furhat.get_gestures()
    print(gestures)

    print("Done")
    await furhat.disconnect()

asyncio.run(main())