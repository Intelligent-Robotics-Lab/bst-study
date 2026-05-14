from furhat_realtime_api import AsyncFurhatClient
import asyncio

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
# List of known working parameters (just the list I have confirmed works):
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