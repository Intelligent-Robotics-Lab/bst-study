from furhat_realtime_api import AsyncFurhatClient
import asyncio
import random

"""This file contains all of the helper functions that get called into the generic behavior function"""

async def connect_furhat(IP_ADDRESS):
    furhat = AsyncFurhatClient(IP_ADDRESS)
    await furhat.connect()
    print("Connected")
    return furhat

async def start_gesture(furhat, gesture, intensity, duration, number_repeat):
    # List of Gestures: BigSmile, Blink, BrowFrown, BrowRaise, CloseEyes, ExpressAnger, ExpressDisgust, ExpressFear, ExpressSad, GazeAway, Nod, Oh, OpenEyes, Roll, Shake, Smile, Surprise, Thoughtful, Wink
    for _ in range(number_repeat):
        await furhat.request_gesture_start(
            name=gesture, 
            intensity = intensity,
            duration= duration
        )
        await asyncio.sleep(duration)

async def speak_text(furhat, message):
    try:
        await furhat.request_speak_text(text=message, wait=True, abort=False)

        await asyncio.sleep(0.5)

    except Exception as e:
        print("[WARN] speak_text:", e)

"""Mapping high-level function names to low-level Furhat parameters."""
# "JAW_OPEN", "SMILE_OPEN", "SMILE_CLOSED", "EYEBROW_LARGER", "BLINK_LEFT", "BLINK_RIGHT", "BROW_IN_LEFT", "BROW_IN_RIGHT", "EYEBROW_UP", "EYEBROW_DOWN"
face_param_mapping = {
    "Happy": {
        "SMILE_CLOSED": 1.0,
        "EYEBROW_UP": 0.75,
        "BROW_IN_LEFT": 0.3,
        "BROW_IN_RIGHT": 0.3,
        "JAW_OPEN": 0.0
    },
    "VeryHappy": {
        "SMILE_OPEN": 0.75,
        "EYEBROW_UP": 0.75,
        "BROW_IN_LEFT": 0.0,
        "BROW_IN_RIGHT": 0.0,
    },
    "Angry": {
        "BROW_IN_LEFT": 1.0,
        "BROW_IN_RIGHT": 1.0,
        "EYEBROW_DOWN": 0.75,
        "SMILE_CLOSED": 0.0,
        "SMILE_OPEN": 0.0,
    },
    "Sad": {
        "BROW_IN_LEFT": 1.0,
        "BROW_IN_RIGHT": 1.0,
        "EYEBROW_UP": 0.5,
        "SMILE_CLOSED": 0.0,
        "FROWN_CLOSED": 1.0,
    },
    "Neutral": {
        "SMILE_CLOSED": 0.0,
        "SMILE_OPEN": 0.0,
        "BROW_IN_LEFT": 0.0,
        "BROW_IN_RIGHT": 0.0,
        "JAW_OPEN": 0.0
    },
    "Surprised": {
        "JAW_OPEN": 1.0,
        "EYEBROW_UP": 1.25,
        "BROW_IN_LEFT": 0.2,
        "BROW_IN_RIGHT": 0.2,
    },
    "Fear": {
        "JAW_OPEN": 0.8,
        "EYEBROW_UP": 1.0,
        "BROW_IN_LEFT": 0.6,
        "BROW_IN_RIGHT": 0.6,
        "SMILE_OPEN": 0.0,
        "SMILE_CLOSED": 0.0
    },
    "Disgust": {
        "BROW_IN_LEFT": 0.8,
        "BROW_IN_RIGHT": 0.8,
        "EYEBROW_UP": 0.0,
        "SMILE_CLOSED": 0.0,
        "SMILE_OPEN": 0.0,
        "JAW_OPEN": 0.2
    }
}

"""Maps the emotion label to the face parameters above."""
def resolve_face_params(face_expression: str):
    return face_param_mapping.get(
        face_expression,
        face_param_mapping["Neutral"])

"""Function to hold the face expression for a request duration."""
async def hold_face_expressions(furhat, face_params, duration=5):
    end_time = asyncio.get_event_loop().time() + duration

    while asyncio.get_event_loop().time() < end_time:
        await furhat.request_face_params(face_params)

        await asyncio.sleep(0.25)

"""Scales the facial parameters by a percentage factor. For example an intensity of 0.5 represents 50% of the max features found above."""
def scale_face_params(face_params, intensity: float):
    # Scales all face parameters by intensity (0-1)
    return{
        k: v * intensity
        for k, v in face_params.items()
    }

"""Function to smoothly switch facial expression without snapping. Still a work in progress."""
async def switch_face(furhat, face_params, duration=2.0, intensity=1.0):
    scaled = scale_face_params(face_params, intensity)

    end_time = asyncio.get_event_loop().time() + duration

    while asyncio.get_event_loop().time() < end_time:
        try:
            await furhat.request_face_params(scaled)
        except Exception as e:
            print("[WARN] face update failed:", e)
            break

        await asyncio.sleep(0.25)

"""Function to add in active listening when listening is set. Work in progress, not yet implemented."""
async def active_listening_loop(furhat, embodiment, stop_event):
    try:
        while not stop_event.is_set():
            try:
                await furhat.request_gesture(name="Nod", intensity=0.25, duration=0.5, repetitions=1)
            except:
                pass

            try:
                await furhat.request_attend_location(
                    x=random.uniform(-0.05, 0.05),
                    y=0,
                    z=1
                )
            except:
                pass

            await asyncio.sleep(random.uniform(4, 7))

    except asyncio.CancelledError:
        pass

"""Function to map keywords to fixed positions, just for "robot" as of now. Allows them to attend to each other reliably in the modeling phase."""
def resolve_look_target(embodiment, target):

    LOOK_MAP = {
        "trainer": {
            "robot":   {"x": -1.25, "y": 0.0, "z": 1.0},
            "neutral": {"x": 0.0,  "y": 0.0, "z": 1.0},
        },
        "kid": {
            "robot":   {"x": 1.5,  "y": 0.0, "z": 1.0},
            "neutral": {"x": 0.0,  "y": 0.0,  "z": 1.0},
        }
    }

    return LOOK_MAP.get(embodiment, LOOK_MAP["trainer"]).get(target, LOOK_MAP["trainer"]["neutral"])

"""Function to track the user and have the robots gaze follow the user throughout the interaction."""
async def track_user_loop(furhat, embodiment, stop_event, refresh_rate=0.5):

    print(f"[TRACK LOOP STARTED] {embodiment}")

    try:
        while not stop_event.is_set():

            await furhat.request_attend_user()

            await asyncio.sleep(refresh_rate)

    except asyncio.CancelledError:
        print(f"[TRACK LOOP CANCELLED] {embodiment}")

    except Exception as e:
        print(f"[TRACK LOOP ERROR] {e}")

"""Function to stop the tracking loop and save necessary parameters."""
async def stop_tracking(embodiment, tracking_task, tracking_stop_event):
    print("f[STOP TRACKING] {embodiment}")
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

"""Function to use LEDs to indicate turn-taking during the rehearsal. It helps to acknowledge inputs and limit confusion."""
async def show_turn(furhat, embodiment, color_override, duration=2.0,):
    try:

        if embodiment == "trainer":
            color = "#00BB00"

        elif embodiment == "kid":
            color = "#4882FF"

        else:
            color = "#FFFFFF"

        color = color_override
        end_time = (asyncio.get_event_loop().time() + duration)

        while (asyncio.get_event_loop().time() < end_time):

            await furhat.request_led_set(color)

            await asyncio.sleep(0.25)

        await furhat.request_led_set("#000000")

    except Exception as e:
        print("[LED ERROR]", e)
