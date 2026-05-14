import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior

"""This file contains the behavior library for the Furhat agent. At its present state"""
async def generic_behavior(furhat, text, duration_text, text_repeats, head_gesture, intensity, duration, num_repeats, attention_target, face_expression, face_intensity, listening: bool, interrupt: bool, gesture_timing):
    if interrupt: 
        await furhat.request_speak_stop()

    if listening:
        await furhat.request_listen_start()
    else:
        await furhat.request_listen_stop()

    gaze_task = None
    gaze_stop = None

    if attention_target == "user":
        gaze_stop = asyncio.Event()
        gaze_task = asyncio.create_task(
            behavior.follow_user_gaze(furhat, gaze_stop)
        )
    elif isinstance(attention_target, str):
        await furhat.request_attend_user(attention_target)
    else:
        await furhat.request_attend_user()
        
    # Set face before speech
    if face_expression is not None:
        new_face_params = behavior.resolve_face_params(face_expression)
        await behavior.switch_face(furhat, new_face_params, intensity=face_intensity)
                                 
    gesture_task = None

    if gesture_timing == "before" and head_gesture is not None:
        await behavior.start_gesture(furhat=furhat, gesture=head_gesture, intensity=intensity, duration=duration, number_repeat=num_repeats)

    elif gesture_timing == "during" and head_gesture is not None:
        gesture_task = asyncio.create_task(
            behavior.start_gesture(furhat=furhat, gesture=head_gesture, intensity=intensity, duration=duration, number_repeat=num_repeats))
    
    elif gesture_timing == "after" and head_gesture is not None:
        pass

    await behavior.speak_text(furhat=furhat, message=text, duration=duration_text, number_repeat=text_repeats)

    # gesture finishes if it was running during the speech
    if gesture_task is not None:
        await gesture_task

    if gesture_timing == "after" and head_gesture is not None:
        await behavior.start_gesture(furhat=furhat, gesture=head_gesture, intensity=intensity, duration=duration, number_repeat=num_repeats)

    # Stop the gaze behavior
    if gaze_task is not None:
        gaze_stop.set()
        await gaze_task

# Will be deleted in future updates, placeholders for now but the generic function above will likely be the only handler for the agent layer
async def nr_problem_behavior(furhat):
    await asyncio.gather(
        behavior.start_gesture(furhat=furhat, gesture="Shake", intensity=5, duration=1, number_repeat=3),
        behavior.speak_text(furhat=furhat, message="NO", number_repeat=3, duration=1)
    )

    await asyncio.gather(
        behavior.start_gesture(furhat=furhat, gesture="GazeAway", intensity=3, duration=3, number_repeat=1),
        behavior.speak_text(furhat=furhat, message="I don't want to", number_repeat=1, duration=2)
    )

async def pr_problem_behavior(furhat):
    await asyncio.gather(
        behavior.start_gesture(furhat=furhat, gesture="Nod", intensity=3, duration=1, number_repeat=2),
        behavior.speak_text(furhat=furhat, message="I want the ball give me give me the ball", number_repeat=1, duration=3)
    )

async def baseline_behavior(furhat):
    await asyncio.gather(
        behavior.start_gesture(furhat=furhat, gesture="Smile", intensity=3, duration=3, number_repeat=1),
        behavior.speak_text(furhat=furhat, message="I am happy to be here", number_repeat=1, duration=3)
    )