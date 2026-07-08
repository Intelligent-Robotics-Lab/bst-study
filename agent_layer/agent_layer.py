from agent_layer.Furhat.Exe.furhat_execute import FurhatBehavior as FurhatExe
from agent_layer.Furhat.Lib.furhat_data_translate import translate_packet_furhat
from agent_layer.Unreal.Exe.unreal_execute import (
    UnrealBehavior as UnrealExe
)

from agent_layer.Unreal.Lib.unreal_data_translate import (
    translate_packet_unreal
)
async def agent_layer(agent_type, embodiment, packet):
    """Main entry point for the agent layer. Translates the incoming packet into the appropriate format for the specified agent type and executes the behavior."""

    if agent_type == "Furhat":        
        furhat_args = translate_packet_furhat(packet)
        await FurhatExe(embodiment=embodiment, packet=furhat_args).execute()
    if agent_type == "Unreal":

        unreal_args = (
            translate_packet_unreal(packet)
        )

        await UnrealExe(
            embodiment=embodiment,
            packet=unreal_args
        ).execute()