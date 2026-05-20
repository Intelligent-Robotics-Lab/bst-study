import asyncio
from dataclasses import dataclass
from typing import Optional

from Perception.perception_client import PerceptionClient


@dataclass
class InteractionState:
    latest_transcript: Optional[str] = None
    latest_emotion: Optional[str] = None
    latest_emotion_confidence: Optional[float] = None


class SampleInteractionAgent:
    def __init__(self, silence_timeout=5.0):
        self.state = InteractionState()

        # speech accumulation
        self.partial_buffer = []
        self.silence_timeout = silence_timeout
        self.silence_task = None

    def handle_asr(self, payload: dict):
        transcript = payload.get("transcript")

        if not transcript:
            return

        print(f"[ASR PARTIAL] {transcript}")

        # append new chunk
        self.partial_buffer.append(transcript)

        # reset silence timer
        if self.silence_task and not self.silence_task.done():
            self.silence_task.cancel()

        self.silence_task = asyncio.create_task(
            self._finalize_after_silence()
        )

    async def _finalize_after_silence(self):
        try:
            await asyncio.sleep(self.silence_timeout)

            # concatenate everything
            full_transcript = " ".join(self.partial_buffer).strip()

            # clear buffer
            self.partial_buffer.clear()

            if full_transcript:
                self.state.latest_transcript = full_transcript

                print(f"\n[FINAL TRANSCRIPT] {full_transcript}\n")

                self._react()

        except asyncio.CancelledError:
            # expected when speech continues
            pass

    def handle_emotion(self, payload: dict):
        prediction = payload.get("prediction") or {}
        label = prediction.get("dominant_label")
        confidence = prediction.get("confidence")

        if label:
            self.state.latest_emotion = label
            self.state.latest_emotion_confidence = confidence
            #print(f"[EMOTION] {label} ({confidence})")

    def _react(self):
        transcript = (self.state.latest_transcript or "").lower()
        emotion = (self.state.latest_emotion or "").lower()

        if "hello" in transcript:
            if emotion in {"sad", "fear", "angry"}:
                print("[AGENT] Hi. You sound like you may need support. I’m here.")
            else:
                print("[AGENT] Hello. Good to see you.")
            return

        if "start task" in transcript:
            if emotion in {"fear", "sad"}:
                print("[AGENT] We can start gently. I’ll guide you step by step.")
            else:
                print("[AGENT] Great. Starting the task now.")
            return

        if "i am confused" in transcript or "help me" in transcript:
            print("[AGENT] I noticed that. Let me slow down and explain the next step.")
            return

        if "stop" in transcript:
            print("[AGENT] Stopping interaction.")
            return


async def main():
    client = PerceptionClient(
        server_host="141.210.88.210",
        server_port=8000
    )

    agent = SampleInteractionAgent(silence_timeout=2.0)

    async for event in client.events():
        event_type = event.get("event_type")
        payload = event.get("payload", {})

        if event_type == "asr_update":
            agent.handle_asr(payload)

        # elif event_type == "emotion_update":
        #     agent.handle_emotion(payload)


if __name__ == "__main__":
    asyncio.run(main())