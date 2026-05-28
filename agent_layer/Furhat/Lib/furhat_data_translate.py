"""Function to translate the data packets from the expression module into a usable format for the Furhat robot."""
def translate_packet_furhat(packet):

    speech = packet.get("speech") or {}
    nonverbals = packet.get("nonverbals", [])
    listening = packet.get("listening", False)
    interrupt = packet.get("interrupt", False)

    text = speech.get("text")
    style = speech.get("style", "neutral")
    volume = speech.get("volume", 1)

    # Estimate speech duration
    if text:
        duration_text = max(
            len(text.split()) * 0.45,
            1.0
        )
    else:
        duration_text = 0

    # =====================================================
    # DEFAULT OUTPUT FORMAT
    # =====================================================

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
            "gaze": [],
            "gesture": [],
            "led": [],
        },

        "attention_target": "user",
        "listening": listening,
    }

    gaze_override = None

    # =====================================================
    # TRANSLATE NONVERBALS
    # =====================================================

    for nv in nonverbals:

        # Safety check
        if not isinstance(nv, dict):
            print(
                "[WARN] Invalid nonverbal:",
                nv
            )
            continue

        channel = nv.get("channel")
        action = nv.get("action")

        entry = {
            "action": action,
            "intensity": nv.get(
                "intensity",
                1.0
            ),
            "duration": nv.get(
                "duration",
                1.0
            ),
            "repeats": nv.get(
                "repeats",
                1
            ),
            "timing": nv.get(
                "timing",
                "during"
            ),
            "keep_moving": nv.get(
                "keep_moving",
                False
            ),
        }

        # ==========================================
        # HEAD
        # ==========================================

        if channel == "head":

            output["nonverbals"]["head"].append(
                entry
            )

        # ==========================================
        # FACE
        # ==========================================

        elif channel == "face":

            output["nonverbals"]["face"].append(
                entry
            )

        # ==========================================
        # GAZE
        # ==========================================

        elif channel == "gaze":

            output["nonverbals"]["gaze"].append(
                entry
            )

            if action in (
                "robot",
                "user",
                "neutral",
            ):
                gaze_override = action

        # ==========================================
        # GESTURE
        # ==========================================

        elif channel == "gesture":

            output["nonverbals"]["gesture"].append(
                entry
            )

        # ==========================================
        # LED
        # ==========================================

        elif channel == "led":

            entry["color"] = nv.get(
                "color",
                "#FFFFFF"
            )

            entry["brightness"] = nv.get(
                "brightness",
                1.0
            )

            output["nonverbals"]["led"].append(
                entry
            )

    # =====================================================
    # ATTENTION OVERRIDE
    # =====================================================

    if gaze_override is not None:

        if gaze_override == "robot":

            output["attention_target"] = (
                "robot"
            )

        elif gaze_override == "user":

            output["attention_target"] = (
                "user"
            )

        else:

            output["attention_target"] = (
                "neutral"
            )

    return output