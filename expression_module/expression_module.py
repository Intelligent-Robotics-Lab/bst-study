import asyncio
import agent_layer.agent_layer as agent_layer

"""Converts generic signals into a high-level expression format to be passed into the agent_layer"""
class ExpressionModule:

    def __init__(self):
        pass

    """Build converts steps into generic packet behavior to be called into the agent_layer for transformation"""
    def build(self, step):

        verbal = step.get("verbal")
        nonverbals = step.get("nonverbals")

        packet = {
            "speech": self._build_speech(verbal),
            "nonverbals": self._build_nonverbals(nonverbals)
        }

        return packet

    def _build_speech(self, verbal):

        if verbal is None:
            return None

        return {
            "text": verbal.get("text"),
            "style": verbal.get("style", "neutral"),
            "volume": verbal.get("volume", 1.0),
            "interrupt": verbal.get("interrupt", False)
        }

    def _build_nonverbals(self, nonverbal):
        output = []

        for nv in nonverbal:

            output.append({
                "channel": nv.get("channel"),
                "action": nv.get("action"),
                "intensity": nv.get("intensity", 1.0), # Intensity for gestures sets the actual intensity, while it is a scalar for facial expressions 0-1
                "duration": nv.get("duration", 1.0),
                "repeats": nv.get("repeats", 1),
                "timing": nv.get("timing", "during")
            })
        
        return output

    # Execution of the agent
    async def execute(self, agent_type, embodiment, packet):

        print("\nExecuting Packet")
        print(packet)

        await agent_layer.agent_layer(agent_type=agent_type, embodiment=embodiment, packet=packet)

    async def fake_agent(self, packet):

        if packet["speech"]:
            print("SPEAK:", packet["speech"]["text"])

        for nv in packet["nonverbals"]:
            print("NONVERBAL:", nv["action"])


