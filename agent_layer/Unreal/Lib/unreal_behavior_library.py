import json
import asyncio
import socket
import time


async def generic_behavior(client, embodiment, packet):
    """
    Sends a behavior packet to an Unreal client.
    """

    message = {
        "embodiment": embodiment,
        "packet": packet
    }

    print("Sending to Unreal:")
    print(json.dumps(message, indent=4))

    await client.send(message)