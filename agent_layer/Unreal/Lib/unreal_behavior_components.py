async def speak_text(avatar, message):

    await avatar.send(
        {
            "type": "speak",
            "text": message
        }
    )
async def play_wav(
    avatar,
    wav_path
):

    await avatar.send(
        {
            "type": "play_wav",
            "path": wav_path
        }
    )
async def set_face(
    avatar,
    emotion,
    intensity=1.0,
    duration=2.0
):

    await avatar.send(
        {
            "type": "face",
            "emotion": emotion,
            "intensity": intensity,
            "duration": duration
        }
    )
async def start_gesture(
    avatar,
    gesture,
    intensity=1.0,
    duration=1.0,
    repeats=1
):

    await avatar.send(
        {
            "type": "gesture",
            "gesture": gesture,
            "intensity": intensity,
            "duration": duration,
            "repeats": repeats
        }
    )
async def look_at(
    avatar,
    target
):

    await avatar.send(
        {
            "type": "look_at",
            "target": target
        }
    )
async def start_tracking(
    avatar
):

    await avatar.send(
        {
            "type": "track_user",
            "enabled": True
        }
    )


async def stop_tracking(
    avatar
):

    await avatar.send(
        {
            "type": "track_user",
            "enabled": False
        }
    )