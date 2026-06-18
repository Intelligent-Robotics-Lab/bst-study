import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior

"""This file controls all connection and disconnection for the Furhat. This also has functions that support the choosing of embodiments based upon the scripts."""

FURHAT_TRAINER_IP = "141.210.88.11"
FURHAT_KID_IP = "141.210.88.254"

_furhats = {}

async def initialize_furhat():
    """Connect both robots once at startup"""
    
    print("Connecting trainer...")
    _furhats["trainer"] = await behavior.connect_furhat(FURHAT_TRAINER_IP)

    print("Connecting kid...")
    _furhats["kid"] = await behavior.connect_furhat(FURHAT_KID_IP)

    print("Both Furhats connected.")

def get_furhat(embodiment):
    return _furhats.get(embodiment)

async def shutdown_furhats():
    """Disconnect from connected Furhat robots."""

    for name, furhat in _furhats.items():
        try:
            await furhat.disconnect()
            print(f"Disconnected {name}")
        except Exception as e:
            print(f"[WARN] {name} disconnect failed: {e}")