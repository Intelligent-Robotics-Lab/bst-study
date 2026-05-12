import asyncio
from agent_layer.Furhat.Exe.furhat_execute import FurhatBehavior as FurhatExe
# Inputs required from the expression module:
    # agent_type, embodiment (kid vs. trainer), text, text_duration, text_repeats, head_gesture, intensity, duration, num_repeats, attention_target, face_expression, voice, listening: bool, interrupt: bool, gesture_timing

# Still need to research vocalization and how we can alter the voice sounds

async def agent_layer(agent_type, embodiment, text, duration_text, text_repeats, head_gesture, intensity, duration, num_repeats, attention_target, face_expression, voice, listening: bool, interrupt: bool, gesture_timing):
    if agent_type == "Furhat":
        # Data transformation step required here once formats are decided upon, for now we will assume the paramters are passed in a format that can be directly used by the behavior library
        
        await FurhatExe(embodiment=embodiment, text=text, duration_text=duration_text, text_repeats=text_repeats, head_gesture=head_gesture, intensity=intensity, duration=duration, num_repeats=num_repeats, 
            attention_target=attention_target, face_expression=face_expression, voice=voice, listening=listening, interrupt=interrupt, gesture_timing=gesture_timing).execute()