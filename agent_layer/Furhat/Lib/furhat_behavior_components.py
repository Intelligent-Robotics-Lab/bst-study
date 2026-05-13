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

# Facial paramter mapping for facial expressiveness, expand once we find more parameters
face_param_mapping = {
    "Happy": {
        "JAW_OPEN": 1.5,
        "EYEBROW_LARGER": 1.5,
    },
    "Angry": {
        "JAW_OPEN": 0.5,
        "EYEBROW_LARGER": 0.5,
    },
    "Sad": {
        "JAW_OPEN": 0.5,
        "EYEBROW_LARGER": 0.5,
    },
    "Neutral": {
        "JAW_OPEN": 0.0,
        "EYEBROW_LARGER": 0.0,
    },
    "Suprised": {
        "JAW_OPEN": 0.5,
        "EYEBROW_LARGER": 0.5,
    },
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