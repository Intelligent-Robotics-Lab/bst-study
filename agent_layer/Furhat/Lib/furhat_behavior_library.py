import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_components as behavior

"""This file contains the behavior library for the Furhat agent. At its present state"""
async def generic_behavior(furhat, text, duration_text, text_repeats, head_gesture, intensity, duration, num_repeats, attention_target, face_expression, voice, listening: bool, interrupt: bool, gesture_timing):
    if interrupt: 
        await furhat.request_speak_stop()

    if listening:
        await furhat.request_listen_start()
    else:
        await furhat.request_listen_stop()

    if voice is not None:
        await furhat.request_voice_config(voice_id=voice)

    if attention_target == "user":
        await furhat.request_attend_user()
    elif isinstance(attention_target, str):
        await furhat.request_attend_user(attention_target)
    else:
        await furhat.request_attend_user()
        
    face_task = None

    # Set face before speech
    if face_expression is not None:
        face_params = behavior.resolve_face_params(face_expression)

        # Address the duration variable
        face_task = asyncio.create_task(
            behavior.hold_face_expressions(furhat=furhat, face_params=face_params, duration=duration_text + 1))
                                 
    gesture_task = None

    if gesture_timing == "before" and head_gesture is not None:
        await behavior.start_gesture(furhat=furhat, gesture=head_gesture, intensity=intensity, duration=duration, number_repeat=num_repeats)

    elif gesture_timing == "during" and head_gesture is not None:
        gesture_task = asyncio.create_task(
            behavior.start_gesture(furhat=furhat, gesture=head_gesture, intensity=intensity, duration=duration, number_repeat=num_repeats))
    
    elif gesture_timing == "after" and head_gesture is not None:
        # IMPORTANT: defer execution until after speech
        pass

    await behavior.speak_text(furhat=furhat, message=text, duration=duration_text, number_repeat=text_repeats)

    # gesture finishes if it was running during the speech
    if gesture_task is not None:
        await gesture_task

    if gesture_timing == "after" and head_gesture is not None:
        await behavior.start_gesture(furhat=furhat, gesture=head_gesture, intensity=intensity, duration=duration, number_repeat=num_repeats)

    if face_task is not None:
        await face_task

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