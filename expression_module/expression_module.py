import asyncio
import agent_layer.agent_layer as agent_layer


class ExpressionModule:

    def __init__(self):
        pass

    # ======================================
    # STEP → GENERIC BEHAVIOR PACKET
    # ======================================
    def build(self, step):

        verbal = step.get("verbal")
        nonverbals = step.get("nonverbals", [])[:2]  # HARD LIMIT

        packet = {
            "speech": self._build_speech(verbal),

            "attention": {
                "target": "user"
            },

            "nonverbals": self._build_nonverbals(nonverbals)
        }

        return packet

    # ======================================
    # SPEECH (0–1 verbal rule enforced here)
    # ======================================
    def _build_speech(self, verbal):

        if verbal is None:
            return None

        return {
            "text": verbal["text"],
            "style": "instructional",
            "volume": 0.85,
            "interrupt": False
        }

    # ======================================
    # NONVERBALS (0–2 rule enforced here)
    # ======================================
    def _build_nonverbals(self, nonverbal):
        nv = nonverbal
        output = ({
                # All Generic Inensities are 0-1
                # All Generic Durations are 0-1
                "gesture_action": nv["action"],
                "gesture_intensity": 0.7,
                "gesture_duration": 1.0,
                "gesture_repeats": 1,
                "gesture_timing": "during",
                "face_expression": "Happy",
                "face_emotion_intensity": 0.7,
                "face_timing": "during",
                "gaze_look_at_user": True,
                "gaze_duration": 1.0,
                "gaze_timing": "during"
            })
        return output

    # ======================================
    # EXECUTION (agent layer hook)
    # ======================================
    async def execute(self, packet):

        print("\n--- EXECUTING PACKET ---")
        print(packet)

        # THIS is where agent layer eventually plugs in:
        # await agent_layer.execute(packet)
        await agent_layer.agent_layer(agent_type="Furhat", embodiment="trainer", packet=packet)
        await self.fake_agent(packet)

    async def fake_agent(self, packet):

        if packet["speech"]:
            print("SPEAK:", packet["speech"]["text"])

        for nv in packet["nonverbals"]:
            print("NONVERBAL:", nv["action"])


