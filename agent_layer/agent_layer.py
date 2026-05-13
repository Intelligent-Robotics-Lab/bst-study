import asyncio
from agent_layer.Furhat.Exe.furhat_execute import FurhatBehavior as FurhatExe
# Inputs required from the expression module:
    # agent_type, embodiment (kid vs. trainer), text, text_duration, text_repeats, head_gesture, intensity, duration, num_repeats, attention_target, face_expression, voice, listening: bool, interrupt: bool, gesture_timing

# Still need to research vocalization and how we can alter the voice sounds

async def agent_layer(agent_type, embodiment, packet):

    if agent_type == "Furhat":

        speech = packet.get("speech")
        attention = packet.get("attention")
        nonverbals = packet.get("nonverbals", [])

        text = None
        interrupt = False

        if speech:
            text = speech.get("text")
            interrupt = speech.get("interrupt", False)
        if text:
            duration_text = max(len(text.split()) * 0.45, 1.0)
        else:
            duration_text = 0
        attention_target = "user"

        if attention:
            attention_target = attention.get("target", "user")

        # Default values
        face_expression = None
        head_gesture = None
        intensity = 1.0
        duration = 1.0
        repeats = 1
        gesture_timing = "during"

        # Parse nonverbals
        for nv in nonverbals:

            channel = nv.get("channel")
            action = nv.get("action")

            intensity = nv.get("intensity", 1.0)
            duration = nv.get("duration", 1.0)
            repeats = nv.get("repeats", 1)
            gesture_timing = nv.get("timing", "during")

            if channel == "face":
                face_expression = action

            elif channel == "head":
                head_gesture = action

        await FurhatExe(
            embodiment=embodiment,

            text=text,
            duration_text=duration_text,
            text_repeats=1,

            head_gesture=head_gesture,
            intensity=intensity,
            duration=duration,
            num_repeats=repeats,

            attention_target=attention_target,

            face_expression=face_expression,

            voice="Gregory-Neural (en-US) - Amazon Polly",
            listening=False,
            interrupt=interrupt,

            gesture_timing=gesture_timing
        ).execute()