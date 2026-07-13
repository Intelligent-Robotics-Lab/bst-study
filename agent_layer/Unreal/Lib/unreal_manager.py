from agent_layer.Unreal.Lib.unreal_client import UnrealClient

_avatars = {}


async def initialize_unreal():

    _avatars["trainer"] = UnrealClient(
        "127.0.0.1",
        7777
    )

    _avatars["kid"] = UnrealClient(
        "127.0.0.1",
        7778
    )

    await _avatars["trainer"].connect()
    await _avatars["kid"].connect()

    print("Unreal avatars connected.")


def get_avatar(embodiment):
    return _avatars.get(embodiment)


async def shutdown_unreal():

    for avatar in _avatars.values():
        await avatar.disconnect()