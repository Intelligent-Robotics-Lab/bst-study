import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior

tracking_task = {}
tracking_stop_event = {}

face_task = {}

"""This function turns the cleaned data packet and outputs its paramters onto the agent of choice for Furhat.
One singular function is used to control the behavior of both robots."""
async def generic_behavior(furhat, embodiment, packet):
    # Clean up the packet to make it usable
    speech = packet.get("speech", {})
    nonverbals = packet.get("nonverbals", {})
    attention_target = packet.get("attention_target", "user")
    listening = packet.get("listening", False)

    interrupt = speech.get("interrupt", False)

    # Interrupt handling (unutilized in the current implementation)
    if interrupt:
        try:
            await furhat.request_speak_stop()
        except Exception as e:
            print("[WARN] interrupt failed:", e)

    # Listening function (unutilized currently but looking to add in active listening feature)
    try:
        if listening:
            asyncio.create_task(furhat.request_listen_start())
        else:
            asyncio.create_task(furhat.request_listen_stop())

    except Exception as e:
        print("[WARN] listen toggle failed:", e)

    # Clean up the tracking events
    if embodiment in tracking_stop_event:
        tracking_stop_event[embodiment].set()

    if embodiment in tracking_task:
        old_task = tracking_task[embodiment]

        old_task.cancel()

        try:
            await old_task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("[WARN] tracking cleanup:", e)

    tracking_task.pop(embodiment, None)
    tracking_stop_event.pop(embodiment, None)

    # Attention target tracking for user and robot selections
    try:
        if attention_target == "user":

            print(f"[TRACK USER START] {embodiment}")

            tracking_stop_event[embodiment] = asyncio.Event()

            tracking_task[embodiment] = asyncio.create_task(
                behavior.track_user_loop(furhat, embodiment, tracking_stop_event[embodiment]))

        elif attention_target == "robot":

            target = behavior.resolve_look_target(embodiment, "robot")

            print(f"[ROBOT LOOK] {target}")

            asyncio.create_task(
                furhat.request_attend_location(
                    x=target["x"],
                    y=target["y"],
                    z=target["z"]
                )
            )

        elif attention_target == "neutral":

            target = behavior.resolve_look_target(embodiment, "neutral")

            print(f"[NEUTRAL LOOK] {target}")

            asyncio.create_task(
                furhat.request_attend_location(
                    x=target["x"],
                    y=target["y"],
                    z=target["z"]
                )
            )

        else:
            asyncio.create_task(furhat.request_attend_user())

    except Exception as e:
        print("[WARN] attention failed:", e)

    # Facial expressions
    if nonverbals.get("face"):

        f = nonverbals["face"][0]
        params = behavior.resolve_face_params(f["action"])

        try:
            if embodiment in face_task:
                old = face_task[embodiment]
                old.cancel()

            face_task[embodiment] = asyncio.create_task(
                behavior.switch_face(furhat, params, duration=speech.get("duration_text", 2.0), intensity=f.get("intensity", 1.0)))

        except Exception as e:
            print("[WARN] face failed:", e)

    # Head gestures
    gesture_task = None

    if nonverbals.get("head"):

        g = nonverbals["head"][0]

        if g.get("timing") == "during":

            gesture_task = asyncio.create_task(
                behavior.start_gesture(furhat, g["action"], g.get("intensity", 1.0), g.get("duration", 1.0), g.get("repeats", 1)))

    # Keep speech as the primary synchonization anchor
    text = speech.get("text", "").strip()

    if text:
        try:
            # Removed text duration and number of repeats as inputs from this function
            await behavior.speak_text(furhat=furhat, message=text)

        except Exception as e:
            print("[WARN] speech failed:", e)

    if gesture_task:
        try:
            await gesture_task
        except Exception as e:
            print("[WARN] gesture failed:", e)