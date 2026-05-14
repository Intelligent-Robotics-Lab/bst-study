"""Transforms expression-module packets into Furhat execution arguments."""

def translate_packet_furhat(packet):

    speech = packet.get("speech", {})
    nonverbals = packet.get("nonverbals", [])

    # Speech
    text = speech.get("text")
    style = speech.get("style", "neutral")
    volume = speech.get("volume", 1)
    interrupt = speech.get("interrupt", False)

    # Estimated speech duration
    if text:
        duration_text = max(len(text.split()) * 0.45, 1.0)
    else:
        duration_text = 0

    # Default output
    output = {
        "text": text,
        "style": style,
        "volume": volume,
        "duration_text": duration_text,
        "text_repeats": 1,
        "interrupt": interrupt,

        "head_gesture": None,
        "head_intensity": 0.5,
        "head_duration": 0,
        "head_repeats": 1,
        "head_timing": "during",

        "face_expression": None,
        "face_intensity": 0.5,
        "face_duration": 0,
        "face_timing": "during",

        "gaze_target": "user",
        "gaze_duration": 1.0,
        "gaze_timing": "during",

        "listening": False
    }

    # Nonverbal translator

    for nv in nonverbals:

        channel = nv.get("channel")
        action = nv.get("action")

        intensity = nv.get("intensity", 1.0)
        duration = nv.get("duration", 1.0)
        repeats = nv.get("repeats", 1)
        timing = nv.get("timing", "during")

        if channel == "head":
            output["head_gesture"] = action
            output["head_intensity"] = intensity
            output["head_duration"] = duration
            output["head_repeats"] = repeats
            output["head_timing"] = timing

        elif channel == "face":
            output["face_expression"] = action
            output["face_intensity"] = intensity
            output["face_duration"] = duration
            output["face_timing"] = timing

        elif channel == "gaze":
            output["gaze_target"] = action
            output["gaze_duration"] = duration
            output["gaze_timing"] = timing

    return output