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
            "volume": verbal.get("volume", 60),
            "audio": verbal.get("audio"),
            "interrupt": verbal.get("interrupt", False)
        }

    def _build_nonverbals(self, nonverbals):

        # Handle missing or None safely
        if not nonverbals:
            return []

        # If old dict format is ever passed, flatten it safely
        if isinstance(nonverbals, dict):
            flattened = []
            for channel in ["face", "head", "gaze", "gesture"]:
                items = nonverbals.get(channel, [])
                if isinstance(items, list):
                    flattened.extend(items)
            return flattened

        # Expected new format: list of events
        if isinstance(nonverbals, list):
            output = []

            for nv in nonverbals:
                if not isinstance(nv, dict):
                    continue

                output.append({
                    "channel": nv.get("channel"),
                    "action": nv.get("action"),

                    # Common fields
                    "intensity": nv.get("intensity", 1.0),
                    "duration": nv.get("duration", 1.0),
                    "repeats": nv.get("repeats", 1),
                    "timing": nv.get("timing", "during"),
                    "keep_moving": nv.get("keep_moving", False),

                    # LED specific
                    "color": nv.get("color"),
                    "brightness": nv.get("brightness", 1.0)

                })

            return output

        # Fallback safety
        return []

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


