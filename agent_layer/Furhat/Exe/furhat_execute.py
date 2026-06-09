import agent_layer.Furhat.Lib.furhat_behavior_library as behavior
import agent_layer.Furhat.Lib.furhat_manager as FurhatManager

"""Class for executing all Furhat related behaviors. This is getting called in the agent_layer top file."""

EMBODIMENT_PROFILE = {
    "trainer": {
        "voice": "Danielle-generative (en-US) - Amazon Polly",
        "face_id": "adult - Rene"
    },
    
    "kid": {
        "voice": "AnaNeural (en-US) - Microsoft Azure",
        "face_id": "child - Billy"
    }
}

class FurhatBehavior:
    # Accepts just embodiment and packet for decision making
    def __init__(self, embodiment, packet):
        self.embodiment = embodiment
        self.packet = packet

    async def execute(self):

        furhat = FurhatManager.get_furhat(self.embodiment)

        if furhat is None:
            raise RuntimeError(f"No robot for {self.embodiment}")

        print(f"Executing on Furhat ({self.embodiment})")
        print("[PACKET]", self.packet)

        profile = EMBODIMENT_PROFILE.get(self.embodiment, {})

        voice = profile.get("voice")
        face_id = profile.get("face_id")

        try:
            await furhat.request_voice_config(voice_id=voice)
        except Exception as e:
            print("[WARN] voice:", e)

        try:
            if face_id:
                await furhat.request_face_config(face_id=face_id)
        except Exception as e:
            print("[WARN] face:", e)

        await behavior.generic_behavior(furhat=furhat, embodiment=self.embodiment, packet=self.packet)