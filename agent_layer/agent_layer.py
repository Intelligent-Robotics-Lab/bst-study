import asyncio
from agent_layer.Furhat.Exe.furhat_execute import FurhatBehavior as FurhatExe
from agent_layer.Furhat.Lib.furhat_data_translate import translate_packet_furhat

"""This layer takes in the expression-module arguments and projects them onto the desired agent."""
async def agent_layer(agent_type, embodiment, packet):

    if agent_type == "Furhat":
        furhat_args = translate_packet_furhat(packet)

        await FurhatExe(embodiment=embodiment, text=furhat_args["text"], duration_text=furhat_args["duration_text"], text_repeats=furhat_args["text_repeats"], head_gesture=furhat_args["head_gesture"], intensity=furhat_args["head_intensity"],
            duration=furhat_args["head_duration"], num_repeats=furhat_args["head_repeats"], attention_target=furhat_args["gaze_target"], face_expression=furhat_args["face_expression"], face_intensity=furhat_args["face_intensity"], listening=furhat_args["listening"],
            interrupt=furhat_args["interrupt"], gesture_timing=furhat_args["head_timing"]).execute()