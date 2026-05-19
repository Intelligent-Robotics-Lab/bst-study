from agent_layer.Furhat.Exe.furhat_execute import FurhatBehavior as FurhatExe
from agent_layer.Furhat.Lib.furhat_data_translate import translate_packet_furhat

async def agent_layer(agent_type, embodiment, packet):

    if agent_type == "Furhat":
        furhat_args = translate_packet_furhat(packet)

        await FurhatExe(
            embodiment=embodiment,
            packet=furhat_args
        ).execute()