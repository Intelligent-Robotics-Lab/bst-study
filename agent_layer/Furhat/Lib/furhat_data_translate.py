"""Function to translate the data packets from the expression module into a usable format for the Furhat robot."""
def translate_packet_furhat(packet):

    speech = packet.get("speech") or {}    
    nonverbals = packet.get("nonverbals", [])
    listening = packet.get("listening", False)
    interrupt = packet.get("interrupt", False)

    text = speech.get("text")
    style = speech.get("style", "neutral")
    volume = speech.get("volume", 1)

    # This implementation guesses the text length to pass this variable. The parameter was removed from the function.
    if text:
        duration_text = max(len(text.split()) * 0.45, 1.0)
    else:
        duration_text = 0

    # Default outputs and format
    output = {
        "speech": {
            "text": text,
            "style": style,
            "volume": volume,
            "duration_text": duration_text,
            "text_repeats": 1,
            "interrupt": interrupt,
        },

        "nonverbals": {
            "head": [],
            "face": [],
            "gaze": []
        },

        "attention_target": "user",  # Defaults to user
        "listening": listening
    }

    gaze_override = None

    for nv in nonverbals:

        channel = nv.get("channel")
        action = nv.get("action")

        entry = {
            "action": action,
            "intensity": nv.get("intensity", 1.0),
            "duration": nv.get("duration", 1.0),
            "repeats": nv.get("repeats", 1),
            "timing": nv.get("timing", "during")
        }

        if channel == "head":
            output["nonverbals"]["head"].append(entry)

        elif channel == "face":
            output["nonverbals"]["face"].append(entry)

        elif channel == "gaze":
            output["nonverbals"]["gaze"].append(entry)

            if action in ("robot", "user", "neutral"):
                gaze_override = action

    # Attention override logic
    if gaze_override is not None:
        if gaze_override == "robot":
            output["attention_target"] = "robot"
        elif gaze_override == "user":
            output["attention_target"] = "user"
        else:
            output["attention_target"] = "neutral"

    return output