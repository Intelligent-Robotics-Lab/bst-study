from furhat_realtime_api import AsyncFurhatClient
import asyncio
import random

async def connect_furhat(IP_ADDRESS):
    furhat = AsyncFurhatClient(IP_ADDRESS)
    await furhat.connect()
    print("Connected")
    return furhat

async def start_gesture(furhat, gesture, intensity, duration, number_repeat):
    # List of Gestures: BigSmile, Blink, BrowFrown, BrowRaise, CloseEyes, ExpressAnger, ExpressDisgust, ExpressFear, ExpressSad, GazeAway, Nod, Oh, OpenEyes, Roll, Shake, Smile, Suprise, Thoughtful, Wink
    for _ in range(number_repeat):
        await furhat.request_gesture_start(
            name=gesture, 
            intensity = intensity,
            duration= duration
        )
        await asyncio.sleep(duration)

async def speak_text(furhat, message, duration, number_repeat):
    for _ in range(number_repeat):
        await furhat.request_speak_text(message)
        await asyncio.sleep(duration)

# Facial paramter mapping for facial expressiveness
# "JAW_OPEN", "SMILE_OPEN", "SMILE_CLOSED", "EYEBROW_LARGER", "BLINK_LEFT", "BLINK_RIGHT", "BROW_IN_LEFT", "BROW_IN_RIGHT", "EYEBROW_UP": 1.5
face_param_mapping = {
    "Happy": {
        "SMILE_CLOSED": 1.25,
        "EYEBROW_UP": 1.0,
        "BROW_IN_LEFT": 0.1,
        "BROW_IN_RIGHT": 0.1,
    },

    "Angry": {
        "BROW_IN_LEFT": 1.0,
        "BROW_IN_RIGHT": 1.0,
        "SMILE_CLOSED": 0.0,
        "EYEBROW_UP": 0.5,
        "JAW_OPEN": 0.5,
    },

    "Sad": {
        "BROW_IN_LEFT": 0.75,
        "BROW_IN_RIGHT": 0.75,
        "EYEBROW_UP": 0.0,
        "SMILE_CLOSED": 0.05,
        "JAW_OPEN": 0.25,
    },

    "Neutral": {
        "SMILE_CLOSED": 0.0,
        "BROW_IN_LEFT": 0.0,
        "BROW_IN_RIGHT": 0.0,
        "EYEBROW_UP": 0.0,
        "JAW_OPEN": 0.0,
    },

    "Suprised": {
        "JAW_OPEN": 0.75,
        "EYEBROW_UP": 1.0,
        "BROW_IN_LEFT": 0.25,
        "BROW_IN_RIGHT": 0.25,
    }
}

def resolve_face_params(face_expression: str):
    return face_param_mapping.get(
        face_expression,
        face_param_mapping["Neutral"])

async def hold_face_expressions(furhat, face_params, duration=5):
    end_time = asyncio.get_event_loop().time() + duration

    while asyncio.get_event_loop().time() < end_time:
        await furhat.request_face_params(face_params)

        await asyncio.sleep(0.25)

def scale_face_params(face_params, intensity: float):
    # Scales all face parameters by intensity (0-1)
    return{
        k: v * intensity
        for k, v in face_params.items()
    }

async def switch_face(furhat, face_params, intensity=1.0):
    # Clear the previous expression by setting everything to neutral
    reset_face_parms = {
        "SMILE_CLOSED": 0.0,
        "SMILE_OPEN": 0.0,
        "JAW_OPEN": 0.0,
        "EYEBROW_UP": 0.0,
        "BROW_IN_LEFT": 0.0,
        "BROW_IN_RIGHT": 0.0
    }

    await furhat.request_face_params(reset_face_parms)
    await asyncio.sleep(0.1)

    scaled = scale_face_params(face_params, intensity)

    await furhat.request_face_params(scaled)

async def follow_user_gaze(furhat, stop_event):
    while not stop_event.is_set():
        await furhat.request_attend_user()
        await asyncio.sleep(1.0) # refresh rate

async def active_listening_loop(furhat, embodiment, stop_event):
    try:
        while not stop_event.is_set():

            try:
                await furhat.request_gesture(
                    name="Nod",
                    intensity=0.25,
                    duration=0.5,
                    repetitions=1
                )
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

def resolve_look_target(embodiment, target):
    """
    Fixed gaze map (NO user detection needed for robot/trainer split)
    """

    LOOK_MAP = {
        "trainer": {
            "robot":   {"x": -1.0, "y": 0.0, "z": 1.0},
            "neutral": {"x": 0.0,  "y": 0.0, "z": 1.0},
        },
        "kid": {
            "robot":   {"x": 1.0,  "y": 0.0, "z": 1.0},
            "neutral": {"x": 0.0,  "y": 0.0,  "z": 1.0},
        }
    }

    return LOOK_MAP.get(embodiment, LOOK_MAP["trainer"]).get(target, LOOK_MAP["trainer"]["neutral"])

import asyncio

async def track_user_loop(furhat, embodiment, stop_event):
    """
    Active gaze tracking loop (user only)
    """

    print(f"[TRACK LOOP STARTED] {embodiment}")

    try:
        while not stop_event.is_set():

            # keeps attention on detected user
            await furhat.request_attend_user()

            # small interval = smooth but not spammy
            await asyncio.sleep(3.5)

    except asyncio.CancelledError:
        print(f"[TRACK LOOP CANCELLED] {embodiment}")

    except Exception as e:
        print(f"[TRACK LOOP ERROR] {e}")
