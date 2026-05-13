import asyncio
import agent_layer.Furhat.Lib.furhat_behavior_library as behavior
import agent_layer.Furhat.Lib.furhat_behavior_components as components

FURHAT_KID_IP = "141.210.88.254"
FURHAT_TRAINER_IP = "141.210.88.254"

class FurhatBehavior:
    def __init__(self, embodiment, text, duration_text, text_repeats, head_gesture, intensity, duration, num_repeats, attention_target, face_expression, voice, listening: bool, interrupt: bool, gesture_timing):
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
        self.voice = voice
        self.listening = listening
        self.interrupt = interrupt
        self.gesture_timing = gesture_timing

    async def execute(self):
        if self.embodiment == "kid":
            furhat = await components.connect_furhat(FURHAT_KID_IP)
            print("Connected to Furhat kid")
        elif self.embodiment  == "trainer":
            furhat = await components.connect_furhat(FURHAT_TRAINER_IP)
            print("Connected to Furhat trainer")
        
        await behavior.generic_behavior(furhat=furhat, text=self.text, duration_text=self.duration_text, text_repeats=self.text_repeats, head_gesture=self.head_gesture, intensity=self.intensity, duration=self.duration, num_repeats=self.num_repeats, attention_target=self.attention_target, face_expression=self.face_expression, voice=self.voice, listening=self.listening, interrupt=self.interrupt, gesture_timing=self.gesture_timing)

        furhat.disconnect()
        print("Disconnected from Furhat " + self.embodiment)