import json
import asyncio
from expression_module.expression_module import ExpressionModule

from Perception.perception_client import PerceptionClient
from Perception.sample_interaction import SampleInteractionAgent


class Modeling:

    def __init__(self, agent=None):
        self.agent = agent

        # State locks
        self.is_speaking = False
        self.in_checkpoint = False
        self.last_transcript = None

    # Perception pieline (same as modeling and DTT)
    async def run_perception(self, client, agent):

        async for event in client.events():

            event_type = event.get("event_type")
            payload = event.get("payload", {})

            # Global speech block to prevent ASR triggering while speaking
            if self.is_speaking:
                continue

            if event_type == "asr_update":
                agent.handle_asr(payload)

            elif event_type == "emotion_update":
                agent.handle_emotion(payload)

    # Main execution loop
    async def execute(self):

        print("\n[MODELING] Starting module...")

        with open("data/modeling_data.json", "r") as f:
            steps = json.load(f)["steps"]

        expr = ExpressionModule()

        agent = SampleInteractionAgent(silence_timeout=2.0)

        client = PerceptionClient(server_host="141.210.88.210", server_port=8000)

        perception_task = asyncio.create_task(self.run_perception(client, agent))

        current_index = 0

        try:
            while current_index < len(steps):

                step = steps[current_index]

                # Debug state
                print("\n-----------------------------------")
                print(f"[INDEX] {current_index}/{len(steps)}")
                print(f"[STEP TYPE] {step.get('type')}")
                print(f"[SPEAKING] {self.is_speaking}")
                print(f"[CHECKPOINT LOCK] {self.in_checkpoint}")
                print(f"[LAST TRANSCRIPT] {self.last_transcript}")
                print("-----------------------------------")

                # Checkpoint handling
                if step.get("type") == "checkpoint":
                    action = await self.handle_checkpoint(step, expr, agent)

                    if action == "repeat":
                        section = step["section"]
                        current_index = self.find_section_start(steps, section)
                        continue

                    current_index += 1
                    continue

                # Normal execution
                packet = expr.build(step)

                embodiment = step.get("embodiment")
                if not embodiment:
                    current_index += 1
                    continue

                # Speech lock-start
                self.is_speaking = True

                # Reset transcripts before speech
                agent.state.latest_transcript = None
                self.last_transcript = None

                print(f"[EXECUTING] {embodiment}")

                await expr.execute(
                    agent_type=self.agent,
                    embodiment=embodiment,
                    packet=packet
                )
                # Speech lock-end
                self.is_speaking = False
                print("[SPEAKING] OFF")

                current_index += 1

        finally:
            perception_task.cancel()

        print("\n[MODELING COMPLETE]")

    # Checkpoint logic with ASR-based instruction understanding
    async def handle_checkpoint(self, step, expr, agent):

        section = step["section"]

        print("\n--------------------------------")
        print(f"[CHECKPOINT] {section}")
        print("[WAITING FOR] continue / repeat")
        print("--------------------------------")

        self.in_checkpoint = True

        timeout = 0

        try:

            while timeout < 60:

                # Hard ASR block during speech
                if self.is_speaking:
                    await asyncio.sleep(0.1)
                    continue

                transcript = agent.state.latest_transcript

                if transcript:
                    print(f"[ASR RAW] {transcript}")

                # Ignore duplicates
                if not transcript or transcript == self.last_transcript:
                    await asyncio.sleep(0.1)
                    timeout += 1
                    continue

                self.last_transcript = transcript
                text = transcript.lower()

                print(f"[CHECKPOINT INPUT] {text}")

                # Intent parsing
                if "continue" in text:
                    print("[INTENT] continue")
                    await self.say_checkpoint_ack(expr, "continue")
                    return "continue"

                if "repeat" in text or "again" in text:
                    print("[INTENT] repeat")
                    await self.say_checkpoint_ack(expr, "repeat")
                    return "repeat"

                print("[INTENT] unclear → clarifying")

                await self.say_clarification(expr, agent)

                agent.state.latest_transcript = None
                self.last_transcript = None

                timeout += 1

        finally:
            self.in_checkpoint = False

        print("[CHECKPOINT TIMEOUT] default continue")
        return "continue"

    # Clarification prompt
    async def say_clarification(self, expr, agent):

        print("[TRAINER] clarification triggered")

        packet = {
            "embodiment": "trainer",
            "verbal": {
                "text": "I'm sorry, I didn't catch that. Can you tell me continue or repeat?"
            },
            "nonverbals": [
                {
                    "channel": "face",
                    "action": "Neutral",
                    "intensity": 0.5,
                    "duration": 1.0,
                    "timing": "during"
                }
            ]
        }

        self.is_speaking = True

        await expr.execute(
            agent_type=self.agent,
            embodiment="trainer",
            packet=expr.build(packet)
        )

        self.is_speaking = False

    # Section finder
    def find_section_start(self, steps, section):

        for i, step in enumerate(steps):
            if step.get("section") == section:
                return i

        return 0

    async def say_checkpoint_ack(self, expr, intent):

        if intent == "repeat":

            packet = {
                "embodiment": "trainer",
                "verbal": {
                    "text": "Okay! Repeating that section again."
                },
                "nonverbals": []
            }

        else:

            packet = {
                "embodiment": "trainer",
                "verbal": {
                    "text": "Okay! Moving on."
                },
                "nonverbals": []
            }

        self.is_speaking = True

        await expr.execute(
            agent_type=self.agent,
            embodiment="trainer",
            packet=expr.build(packet)
        )

        self.is_speaking = False