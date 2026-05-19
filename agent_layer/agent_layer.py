from agent_layer.Furhat.Exe.furhat_execute import FurhatBehavior as FurhatExe
from agent_layer.Furhat.Lib.furhat_data_translate import translate_packet_furhat

"""This is the top level of the agent layer, this is meant to stay vague and allow for the calling of various agents based on the selection in the BST file."""
async def agent_layer(agent_type, embodiment, packet):

    if agent_type == "Furhat":
        furhat_args = translate_packet_furhat(packet)

        await FurhatExe(embodiment=embodiment, packet=furhat_args).execute()