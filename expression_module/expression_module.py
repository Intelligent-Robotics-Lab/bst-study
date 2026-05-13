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
    def _build_nonverbals(self, nonverbals):

        output = []

        for nv in nonverbals:

            output.append({
                "channel": nv["type"],   # head / face / gaze
                "action": nv["action"],
                "intensity": 0.7,
                "duration": 1.0,
                "repeats": 1,
                "timing": "during"
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


