import asyncio
import json
import re
from expression_module.expression_module import ExpressionModule
from Perception.perception_client import PerceptionClient
from Perception.sample_interaction import SampleInteractionAgent

"""This class contains all the helper functions used in the instruction and modeling logic."""
class BaseInteraction:
    def __init__(self, agent=None, wake_word="freeze"):
        self.agent = agent
        self.state = "IDLE"
        self.is_speaking = False
        self.interrupted = False
        self.current_index = 0
        self.current_section = None
        self.last_transcript = None
        self.steps = []
        self.WAKE_WORDS = {"freeze", "free", "breeze", "tree", "trees"}
        self.expr = ExpressionModule()
        self.accepting_input = True

    # Only thing child overrides
    def load_steps(self):
        raise NotImplementedError

    def get_module_name(self):
        return "base"

    async def run_main_loop(self, agent):
        raise NotImplementedError

    """Entry point initializing perception and running the main inference loop"""
    async def execute(self):
        print(f"\n[{self.get_module_name().upper()}] Starting module...")

        self.steps = self.load_steps()

        # Make both robots attend back to neutral first (need to add)

        # ASR detection with 2 second timeout for final transcript
        agent = SampleInteractionAgent(silence_timeout=2.0)

        # Connect to the perception layer using the server
        client = PerceptionClient(server_host="141.210.88.210", server_port=8000)

        task = asyncio.create_task(self.run_perception(client, agent))

        try:
            await self.run_main_loop(agent)
        finally:
            task.cancel()

        print(f"\n[{self.get_module_name().upper()} COMPLETE]")

    """Continuously listens to emotion and ASR events from the perception module"""
    async def run_perception(self, client, agent):
        async for event in client.events():

            event_type = event.get("event_type")
            payload = event.get("payload", {})

            if event_type == "emotion_update":
                agent.handle_emotion(payload)

            elif event_type == "asr_update":
                await self.handle_asr(payload, agent)
    
    """Processes ASR input, handles wake word detection, and forwards valid transcipts."""
    async def handle_asr(self, payload, agent):
        transcript = (payload.get("transcript") or "").lower().strip()
        cleaned = re.sub(r"[^\w\s]", "", transcript)

        if transcript:
            print(f"[ASR] {transcript}")

        tokens = cleaned.split()

        if any(word in tokens for word in self.WAKE_WORDS):
            await self.trigger_freeze()

        if self.is_speaking:
            return

        if not self.accepting_input:
            return

        agent.handle_asr(payload)

    """Triggers interrupt state and provides LED feedback to indicate the word was detected."""
    async def trigger_freeze(self):
        self.interrupted = True

        # LED flashes blue to indicate that freeze was detected
        turn = {
            "embodiment": "trainer",
            "verbal": {"text": ""},
            "nonverbals": [{
                "channel": "led",
                "action": "on",
                "color": "#66A5ED",
                "duration": 2.0
            }]
        }

        await self.expr.execute(agent_type=self.agent, embodiment="trainer", packet=self.expr.build(turn))

    async def signal_listening(self):
        turn = {
            "embodiment": "trainer",
            "verbal": {"text": ""},
            "nonverbals": [{
                "channel": "led",
                "action": "on",
                "color": "#00FF00",
                "duration": 1
            }]
        }

        await self.expr.execute(agent_type=self.agent, embodiment="trainer", packet=self.expr.build(turn))

    """Executes a single step using the expression module and handles embodiment output."""
    async def execute_step(self, step):
        if not step.get("embodiment"):
            return

        self.is_speaking = True
        print(f"[EXECUTING] {step.get('embodiment')}")

        await self.expr.execute(agent_type=self.agent, embodiment=step["embodiment"], packet=self.expr.build(step))

        self.is_speaking = False

    """Handles user navigation commands like continue, repeat step, repeat section, and summary"""
    async def handle_navigation(self, expr, agent, step):
        self.state = "NAVIGATION"
        self.last_transcript = None

        await self.say_text(expr, "Would you like to continue, repeat the step, repeat the section, or hear a summary?")

        self.accepting_input = False

        await asyncio.sleep(0.5) # Wait statement to make sure ASR is cleared before listening to the user

        agent.state.latest_transcript = None
        self.last_transcript = None

        await self.signal_listening() # LED signal to indicate that the robot is now listening

        self.accepting_input = True

        timeout = 0
        clarification_used = False

        while timeout < 80: # Approximately an 8 second timeout
            if self.is_speaking:
                await asyncio.sleep(0.1)
                continue

            if self.interrupted: # In the event the user says the wake word again
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

            if not clarification_used:

                clarification_used = True

                # First and only ask for clarification
                await self.say_text(expr, "Sorry, I didn't understand. Please say continue, repeat, section, or summary.")

                self.accepting_input = False

                await asyncio.sleep(0.5) # Timeout after finishing speaking before input is accepted and LED indicator goes active

                agent.state.latest_transcript = None
                self.last_transcript = None

                await self.signal_listening()

                self.accepting_input = True

                continue

            # In the event of a second incoherent statement
            await self.say_text(expr, "I wasn't able to understand your response, so I will continue. If you wanted something else, please say freeze and ask again.")
            return "continue"

    """Runs interactive multiple=choice question flow."""
    async def handle_knowledge_check(self, step, expr, agent):
        print("[KNOWLEDGE CHECK]")

        question = step.get("question", {})
        feedback = step.get("feedback", {})

        correct_answer = (question.get("correct_answer") or "").lower()

        text = question.get("text", "")
        choices = question.get("choices", [])

        full_question = text + " " + " ".join(choices)

        retries_used = 0

        await self.say_text(expr, full_question)

        self.accepting_input = False

        await asyncio.sleep(0.5)

        agent.state.latest_transcript = None
        self.last_transcript = None

        await self.signal_listening()

        self.accepting_input = True

        timeout = 0

        while True:
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

                self.accepting_input = False

                await asyncio.sleep(0.5)

                agent.state.latest_transcript = None
                self.last_transcript = None

                await self.signal_listening()

                self.accepting_input = True

                timeout = 0
                continue

            transcript = agent.state.latest_transcript

            if not transcript:
                await asyncio.sleep(0.1)
                timeout += 1

                if timeout >= 80: # Approximately an 8 second timeout
                    retries_used += 1

                    # First retry statement if there is a timeout statement
                    if retries_used == 1:
                        await self.say_text(expr, "I didn't hear a response. Please say Option A, Option B, or Option C.")

                        self.accepting_input = False

                        await asyncio.sleep(1.0) # Same wait statement before accepting input

                        agent.state.latest_transcript = None
                        self.last_transcript = None

                        await self.signal_listening()

                        self.accepting_input = True

                        timeout = 0
                        continue

                    # If timeout the second time just give the answer and move on
                    await self.say_text(
                        expr,
                        feedback.get(
                            "incorrect",
                            f"Sorry, the correct answer is Option {correct_answer.upper()}."
                        )
                    )

                    return "timeout"

                continue

            text = transcript.lower().strip()

            if text == self.last_transcript:
                continue

            self.last_transcript = text
            agent.state.latest_transcript = None

            timeout = 0

            print(f"[ANSWER INPUT] {text}")

            detected = self.parse_answer(text)

            if detected not in ["a", "b", "c"]:
                retries_used += 1

                # First retry if answer given but not a valid option
                if retries_used == 1:
                    await self.say_text(expr, "I'm sorry, I didn't catch that. Please say Option A, Option B, or Option C.")

                    self.accepting_input = False

                    await asyncio.sleep(1.0)

                    agent.state.latest_transcript = None
                    self.last_transcript = None

                    await self.signal_listening()

                    self.accepting_input = True

                    continue

                # If retry already used and couldn't decipher the answer move on
                await self.say_text(
                    expr,
                    feedback.get(
                        "incorrect",
                        f"Sorry, the correct answer is Option {correct_answer.upper()}."
                    )
                )
                return "incorrect"

            if detected == correct_answer:

                await self.say_text(
                    expr,
                    feedback.get("correct", "Correct.")
                )
                return "correct"

            await self.say_text(
                expr,
                feedback.get(
                    "incorrect",
                    f"Sorry, the correct answer is Option {correct_answer.upper()}."
                )
            )
            return "incorrect"

    """Converts noisy ASR input into structured multiple-choice answers (A/B/C)"""
    def parse_answer(self, text):
        if not text:
            return None

        text = re.sub(r"[^a-z\s]", "", text.lower().strip())

        tokens = text.split()

        for t in tokens:
            if t in ["a", "b", "c"]:
                return t
            if t == "bee":
                return "b"
            if t == "be":
                return "b"
            if t == "see":
                return "c"

        if " a " in f" {text} ":
            return "a"
        if " b " in f" {text} ":
            return "b"
        if " c " in f" {text} ":
            return "c"

        if text.startswith("a"):
            return "a"
        if text.startswith("b"):
            return "b"
        if text.startswith("c"):
            return "c"

        return None

    """Finds and reads aloud the summary associated with the current section."""
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

    """Speaks text using the expression module while locking speaking state."""
    async def say_text(self, expr, text):
        print(f"[SAY TEXT] {repr(text)}") # Debug print while testing

        text = text or ""

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

    """Finds the first index of a section in the step list for section restart purposes."""
    def find_section_start(self, section):
        for i, step in enumerate(self.steps):
            if step.get("section") == section:
                return i
        return 0