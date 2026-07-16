import asyncio
import agent_layer.Furhat.Lib.furhat_manager as FurhatManager

_furhats = None

async def test():
    global _furhats
    _furhats = await FurhatManager.initialize_furhat()
    print("Furhats connected:", _furhats)

if __name__ == "__main__":
    asyncio.run(test())