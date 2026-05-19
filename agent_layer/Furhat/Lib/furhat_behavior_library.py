import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior

tracking_task = {}
tracking_stop_event = {}


async def generic_behavior(furhat, embodiment, packet):

    speech = packet.get("speech", {})
    nonverbals = packet.get("nonverbals", {})
    attention_target = packet.get("attention_target", "user")
    listening = packet.get("listening", False)
    interrupt = speech.get("interrupt", False)

    if interrupt:
        try:
            await furhat.request_speak_stop()
        except Exception as e:
            print("[WARN] interrupt failed:", e)

    if listening:
        asyncio.create_task(furhat.request_listen_start())
    else:
        asyncio.create_task(furhat.request_listen_stop())

    # Stop tracking event 
    if embodiment in tracking_stop_event:
        tracking_stop_event[embodiment].set()

    if embodiment in tracking_task:
        tracking_task[embodiment].cancel()

    tracking_task.pop(embodiment, None)
    tracking_stop_event.pop(embodiment, None)

    # Attention control
    if attention_target == "user":

        print(f"[TRACK USER START] {embodiment}")

        tracking_stop_event[embodiment] = asyncio.Event()

        tracking_task[embodiment] = asyncio.create_task(
            behavior.track_user_loop(
                furhat,
                embodiment,
                tracking_stop_event[embodiment]
            )
        )

    elif attention_target == "robot":

        target = behavior.resolve_look_target(embodiment, "robot")

        print(f"[ROBOT LOOK] {target}")

        await furhat.request_attend_location(
            x=target["x"],
            y=target["y"],
            z=target["z"]
        )

    elif attention_target == "neutral":

        target = behavior.resolve_look_target(embodiment, "neutral")

        print(f"[NEUTRAL LOOK] {target}")

        await furhat.request_attend_location(
            x=target["x"],
            y=target["y"],
            z=target["z"]
        )

    else:
        await furhat.request_attend_user()

    # Face expression (may need updating)
    if nonverbals.get("face"):
        for f in nonverbals["face"]:
            params = behavior.resolve_face_params(f["action"])
            asyncio.create_task(
                behavior.switch_face(
                    furhat,
                    params,
                    intensity=f.get("intensity", 1.0)
                )
            )

    # Head gesture
    gesture_task = None

    if nonverbals.get("head"):
        g = nonverbals["head"][0]

        if g.get("timing") == "during":
            gesture_task = asyncio.create_task(
                behavior.start_gesture(
                    furhat,
                    g["action"],
                    g.get("intensity", 1.0),
                    g.get("duration", 1.0),
                    g.get("repeats", 1)
                )
            )

    # Speech
    text = speech.get("text", "")
    duration = speech.get("duration_text", 1.0)
    repeats = speech.get("text_repeats", 1)

    await behavior.speak_text(furhat=furhat, message=text, duration=duration, number_repeat=repeats)

    if gesture_task:
        await gesture_task