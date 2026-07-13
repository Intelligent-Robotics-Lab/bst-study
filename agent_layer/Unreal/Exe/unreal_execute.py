import agent_layer.Unreal.Lib.unreal_behavior_library as behavior
import agent_layer.Unreal.Lib.unreal_manager as UnrealManager
from agent_layer.Unreal.Lib.unreal_constants import EMBODIMENT_PROFILE


class UnrealBehavior:

    def __init__(self, embodiment, packet):
        self.embodiment = embodiment
        self.packet = packet

    async def execute(self):

        avatar = UnrealManager.get_avatar(self.embodiment)

        if avatar is None:
            raise RuntimeError(
                f"No Unreal avatar for {self.embodiment}"
            )

        print(f"Executing on Unreal ({self.embodiment})")
        print("[PACKET]", self.packet)

        profile = EMBODIMENT_PROFILE.get(
            self.embodiment,
            {}
        )

        await avatar.send(
            {
                "type": "configure",
                "voice": profile.get("voice"),
                "avatar": profile.get("avatar")
            }
        )

        await behavior.generic_behavior(
            client=avatar,
            embodiment=self.embodiment,
            packet=self.packet
        )