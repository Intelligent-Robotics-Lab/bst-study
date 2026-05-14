import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_library as behavior
import agent_layer.Furhat.Lib.furhat_behavior_components as components

FURHAT_KID_IP = "141.210.88.254"
FURHAT_TRAINER_IP = "141.210.88.11"

EMBODIMENT_PROFILE = {
    "trainer": {
        "voice": "Gregory-Neural (en-US) - Amazon Polly",
        "face_id": "adult - James"
    },
    "kid": {
        "voice": "Ivy-Neural (en-US) - Amazon Polly",
        "face_id": "child - Billy"
    }
}

# This should be reduced down to packet later
class FurhatBehavior:
    def __init__(self, embodiment, text, duration_text, text_repeats, head_gesture, intensity, duration, num_repeats, attention_target, face_expression, face_intensity, listening: bool, interrupt: bool, gesture_timing, voice=None, face_id=None):
        self.embodiment = embodiment
        self.text = text
        self.duration_text = duration_text
        self.text_repeats = text_repeats
        self.head_gesture = head_gesture
        self.intensity = intensity
        self.duration = duration
        self.num_repeats = num_repeats
        self.attention_target = attention_target
        self.face_expression = face_expression
        self.face_intensity = face_intensity
        self.voice = voice
        self.listening = listening
        self.interrupt = interrupt
        self.gesture_timing = gesture_timing
        self.face_id = face_id

    async def execute(self):
        print(f"Connecting to Furhat ({self.embodiment})")

        ip = (
            FURHAT_KID_IP if self.embodiment == "kid"
            else FURHAT_TRAINER_IP
        )

        furhat = await components.connect_furhat(ip)

        print(f"Connected to Furhat ({self.embodiment})")

        await asyncio.sleep(0.1)

        profile = EMBODIMENT_PROFILE.get(self.embodiment, {})

        voice = self.voice or profile.get("voice")
        face_id = self.face_id or profile.get("face_id")

        try:
            await furhat.request_voice_config(voice_id=voice)
        except Exception as e:
            print(f"[WARN] Voice config failed, continuing default voice: {e}")

        try:
            if face_id:
                await furhat.request_face_config(face_id)
        except Exception as e:
            print(f"[WARN] Face config failed: {e}")

        await behavior.generic_behavior(furhat=furhat, text=self.text, duration_text=self.duration_text, text_repeats=self.text_repeats, head_gesture=self.head_gesture, intensity=self.intensity, duration=self.duration, num_repeats=self.num_repeats, attention_target=self.attention_target, face_expression=self.face_expression, face_intensity=self.face_intensity, listening=self.listening, interrupt=self.interrupt, gesture_timing=self.gesture_timing)

        furhat.disconnect()
        print(f"Disconnected from Furhat ({self.embodiment})")