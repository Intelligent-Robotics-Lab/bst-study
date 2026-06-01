import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior

tracking_task = {}
tracking_stop_event = {}
current_attention = {}
face_task = {}

"""This function turns the cleaned data packet and outputs its paramters onto the agent of choice for Furhat.
One singular function is used to control the behavior of both robots."""
async def generic_behavior(furhat, embodiment, packet):
    # Clean up the packet to make it usable
    speech = packet.get("speech") or {}
    nonverbals = packet.get("nonverbals", {})
    attention_target = packet.get("attention_target", "user")
    listening = packet.get("listening", False)

    # Debug print (temporary)
    print(
        f"[PACKET] embodiment={embodiment} "
        f"attention={attention_target}"
        f"text={speech.get('text', '')[:40]}"
    )

    for nv in nonverbals.get("led", []):
        action = nv.get("action", "on")

        if action == "on":
            print("[LED LAYER]", nonverbals.get("led"))
            
            await behavior.show_turn(furhat, embodiment=embodiment,color_override=nv.get("color", "#000000"),duration=nv.get("duration", 2.0),)
            
        elif action == "off":
            await behavior.show_turn(furhat, embodiment=embodiment, color_override=nv.get("color", "#000000"), duration=nv.get("duration", 2.0),)
            
    # Listening function (unutilized currently but looking to add in active listening feature)
    try:
        if listening:
            asyncio.create_task(furhat.request_listen_start())
        else:
            asyncio.create_task(furhat.request_listen_stop())

    except Exception as e:
        print("[WARN] listen toggle failed:", e)

    # Clean up the tracking events
    previous_attention = current_attention.get(embodiment)
    attention_changed = (previous_attention != attention_target)

    if attention_changed:
        await behavior.stop_tracking(embodiment, tracking_task, tracking_stop_event)

    # Attention control
    try:
        if attention_changed:

            if attention_target == "user":

                print(f"[TRACK USER START] {embodiment}")

                tracking_stop_event[embodiment] = asyncio.Event()

                tracking_task[embodiment] = asyncio.create_task(
                    behavior.track_user_loop(furhat, embodiment, tracking_stop_event[embodiment], refresh_rate=0.5))

            else:
                target = behavior.resolve_look_target(embodiment, attention_target)

                print(f"[LOOK TARGET] {attention_target}: {target}")

                await furhat.request_attend_location(
                    x=target["x"],
                    y=target["y"],
                    z=target["z"]
                )

            current_attention[embodiment] = attention_target

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
    after_gesture = None

    if nonverbals.get("head"):

        g = nonverbals["head"][0]

        try:
            if g.get("timing") == "before":

                await behavior.start_gesture(furhat, g["action"], g.get("intensity", 1.0), g.get("duration", 1.0), g.get("repeats", 1))

            elif g.get("timing") == "during":
                gesture_task = asyncio.create_task(
                    behavior.start_gesture(furhat, g["action"], g.get("intensity", 1.0), g.get("duration", 1.0), g.get("repeats", 1))
                )

            elif g.get("timing") == "after":
                after_gesture = g

        except Exception as e:
            print("[WARN] gesture setup failed:", e)

    # Keep speech as the primary synchonization anchor
    text = (speech.get("text") or "").strip()
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

    if after_gesture:
        # Debug print
        print("[AFTER GESTURE STARTING]", after_gesture)

        try:
            await behavior.start_gesture(furhat, after_gesture["action"], after_gesture.get("intensity", 1.0), after_gesture.get("duration", 1.0), after_gesture.get("repeats", 1))
        except Exception as e:
            print("[WARN] after gesture failed", e)