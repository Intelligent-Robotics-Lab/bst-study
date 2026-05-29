import json
import re
import asyncio
from expression_module.expression_module import ExpressionModule
from Perception.perception_client import PerceptionClient
from Perception.sample_interaction import SampleInteractionAgent


class Instruction:
    def __init__(self, agent=None):
        self.agent = agent
        self.state = "LECTURE"
        self.is_speaking = False
        self.interrupted = False
        self.current_index = 0
        self.current_section = None
        self.last_transcript = None
        self.steps = []
        self.WAKE_WORD = "freeze"

    # Perception loop
    async def run_perception(self, client, agent):
        async for event in client.events():

            event_type = event.get("event_type")
            payload = event.get("payload", {})

            if event_type == "emotion_update":
                agent.handle_emotion(payload)

            elif event_type == "asr_update":

                transcript = (payload.get("transcript") or "").lower().strip()

                if transcript:
                    print(f"[ASR] {transcript}")

                # Freeze works all the time
                if self.WAKE_WORD in transcript:
                    print("[WAKE WORD DETECTED]")
                    self.interrupted = True

                # Ignore the speech while the robot is talking (outside of freeze)
                if self.is_speaking:
                    continue

                agent.handle_asr(payload)

    # Execution loop
    async def execute(self):

        print("\n[INSTRUCTION] Starting module...")

        with open("data/instruction_data.json", "r") as f:
            self.steps = json.load(f)["steps"]

        expr = ExpressionModule()
        agent = SampleInteractionAgent(silence_timeout=2.0)

        client = PerceptionClient(server_host="141.210.88.210", server_port=8000)

        perception_task = asyncio.create_task(self.run_perception(client, agent))

        try:
            while self.current_index < len(self.steps):

                step = self.steps[self.current_index]
                self.current_section = step.get("section")

                print(f"\n[INDEX] {self.current_index}")
                print(f"[SECTION] {self.current_section}")
                print(f"[TYPE] {step.get('type')}")
                print(f"[SPEAKING] {self.is_speaking}")

                # Knowledge check questions
                if step.get("type") == "knowledge_check":

                    result = await self.handle_knowledge_check(step, expr, agent)

                    print(f"[QUESTION RESULT] {result}")

                    if result == "repeat_section":
                        self.current_index = self.find_section_start(self.current_section)
                        continue

                    if result == "timeout":
                        self.current_index += 1
                        continue

                    self.current_index += 1
                    continue

                # Normal step execution
                await self.execute_step(step, expr)

                # Navigation interrupt
                if self.interrupted:
                    self.interrupted = False

                    action = await self.handle_navigation(expr, agent, step)

                    if action == "repeat_step":
                        continue

                    elif action == "repeat_section":
                        self.current_index = self.find_section_start(self.current_section)
                        continue

                    elif action == "summary":
                        await self.play_summary(step, expr)
                        continue

                self.current_index += 1

        finally:
            perception_task.cancel()

        print("\n[INSTRUCTION COMPLETE]")

    # Step execution
    async def execute_step(self, step, expr, agent=None):

        embodiment = step.get("embodiment")
        if not embodiment:
            return

        packet = expr.build(step)

        self.is_speaking = True

        print(f"[EXECUTING] {embodiment}")

        await expr.execute(agent_type=self.agent, embodiment=embodiment, packet=packet)

        self.is_speaking = False

    # Stable navigation loop
    async def handle_navigation(self, expr, agent, step):
        self.state = "NAVIGATION"
        self.last_transcript = None

        await self.say_text(expr, "Would you like to continue, repeat the step, repeat the section, or hear a summary?")

        timeout = 0

        while timeout < 120:

            if self.is_speaking:
                await asyncio.sleep(0.1)
                continue

            if self.interrupted:
                self.interrupted = False
                await self.say_text(expr, "Paused. Continue when ready.")
                continue

            transcript = agent.state.latest_transcript

            if not transcript:
                await asyncio.sleep(0.1)
                timeout += 1
                continue

            text = transcript.lower().strip()

            if text == self.last_transcript:
                await asyncio.sleep(0.1)
                continue

            self.last_transcript = text
            agent.state.latest_transcript = None

            print(f"[NAV INPUT] {text}")

            if "continue" in text:
                self.state = "LECTURE"
                return "continue"

            if "summary" in text:
                self.state = "LECTURE"
                return "summary"

            if "section" in text:
                self.state = "LECTURE"
                return "repeat_section"

            if "repeat" in text or "again" in text:
                self.state = "LECTURE"
                return "repeat_step"

            await self.say_text(expr, "Please say: continue, repeat, section, or summary.")

            timeout += 1

        return "continue"

    # Function for handling the knowledge check
    async def handle_knowledge_check(self, step, expr, agent):

        print("[KNOWLEDGE CHECK]")

        question = step.get("question", {})
        feedback = step.get("feedback", {})

        correct_answer = question.get("correct_answer", "").lower()

        text = question.get("text", "")
        choices = question.get("choices", [])

        full_question = text + " " + " ".join(choices)

        attempts = 0

        while attempts < 3:

            await self.say_text(expr, full_question)

            agent.state.latest_transcript = None
            self.last_transcript = None

            timeout = 0

            while timeout < 120:

                if self.is_speaking:
                    await asyncio.sleep(0.1)
                    continue

                if self.interrupted:

                    self.interrupted = False

                    action = await self.handle_navigation(expr, agent, step)

                    if action == "repeat_section":
                        return "repeat_section"

                    if action == "summary":
                        await self.play_summary(step, expr)

                    break

                transcript = agent.state.latest_transcript

                if not transcript:
                    await asyncio.sleep(0.1)
                    timeout += 1
                    continue

                text = transcript.lower().strip()

                if text == self.last_transcript:
                    continue

                self.last_transcript = text
                agent.state.latest_transcript = None

                print(f"[ANSWER INPUT] {text}")

                detected = self.parse_answer(text)

                if detected not in ["a", "b", "c"]:
                    await self.say_text(expr, "I'm sorry, I didn't catch that. Please say A, B, or C clearly.")
                    timeout += 1
                    continue

                if detected == correct_answer:
                    await self.say_text(expr, feedback.get("correct", "Correct."))
                    return "correct"

                await self.say_text(expr, feedback.get("incorrect", "Incorrect."))
                return "incorrect"

            attempts += 1

        await self.say_text(expr, "Let's move on.")
        return "timeout"

    def parse_answer(self, text, question=None):
        if not text:
            return None

        text = text.lower().strip()

        # remove punctuation
        text = re.sub(r"[^a-z\s]", "", text)

        tokens = text.split()

        # Direct letter detection and close resemblence
        for token in tokens:

            # direct letters
            if token in ["a", "b", "c"]:
                return token

            # speech-to-text variants
            if token == "bee":
                return "b"

            if token == "see":
                return "c"

        # Letter anywhere in the string
        if " a " in f" {text} ":
            return "a"

        if " b " in f" {text} ":
            return "b"

        if " c " in f" {text} ":
            return "c"

        # Prefix fallbacks
        if text.startswith("a"):
            return "a"

        if text.startswith("b") or text.startswith("bee"):
            return "b"

        if text.startswith("c") or text.startswith("see"):
            return "c"

        return None

    # Play the summary for the current section
    async def play_summary(self, step, expr):

        current_section = step.get("section")

        summary_text = None

        # Look through all steps for this section
        for s in self.steps:

            if s.get("section") != current_section:
                continue

            summary = s.get("summary")

            if not summary:
                continue

            # Skip disabled summaries
            if isinstance(summary, dict):

                if not summary.get("enabled", False):
                    continue

                summary_text = summary.get("text")

            else:
                summary_text = str(summary)

            # Stop at first valid summary
            if summary_text:
                break

        if not summary_text:
            await self.say_text(expr, "No summary available for this section.")
            return

        await self.say_text(expr, summary_text)

    async def say_text(self, expr, text):
        self.is_speaking = True

        await expr.execute(
            agent_type=self.agent,
            embodiment="trainer",
            packet=expr.build({
                "embodiment": "trainer",
                "verbal": {"text": text},
                "nonverbals": []
            })
        )

        self.is_speaking = False

    def find_section_start(self, section):

        for i, step in enumerate(self.steps):
            if step.get("section") == section:
                return i

        return 0