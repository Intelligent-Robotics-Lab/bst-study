import asyncio
import json
import re
from expression_module.expression_module import ExpressionModule
from Perception.perception_client import PerceptionClient
from Perception.sample_interaction import SampleInteractionAgent

"""This class contains all the helper functions used in the instruction and modeling logic."""
class BaseInteraction:
    def __init__(self, agent=None):
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
        self.led_state = None

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

        # NOTE: future addition to set both robots to attend to neutral when the process is started.

        agent = SampleInteractionAgent(silence_timeout=2.0) # ASR has 2-second timeout for final transcript

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
        cleaned = re.sub(r"[^\w\s]", "", transcript) # Remove any puncutation, used to detect the wake word options

        if transcript:
            print(f"[ASR] {transcript}")

        tokens = cleaned.split()

        if any(word in tokens for word in self.WAKE_WORDS): # Trigger a freeze if any of the wake words are detected
            await self.trigger_freeze()
            return

        if self.is_speaking or not self.accepting_input:
            return

        agent.handle_asr(payload)

    """Function to clean up redundant code in the following functions."""
    async def prepare_for_input(self, agent, delay=0.5):
        self.accepting_input = False

        await asyncio.sleep(delay)

        agent.state.latest_transcript = None
        self.last_transcript = None

        await self.set_led("listening")

        self.accepting_input = True

    """Triggers interrupt state and provides LED feedback to indicate the word was detected."""
    async def trigger_freeze(self):
        print("[FREEZE DETECTED]")

        self.interrupted = True

        await self.set_led("freeze")

    """Function to turn on the green LED when listening"""
    async def signal_listening(self):
        await self.set_led("listening")

    """Executes a single step using the expression module and handles embodiment output."""
    async def execute_step(self, step):
        if not step.get("embodiment"):
            return
        
        await self.set_led("off") # Turn the LED off at the start of a step as the robot speaks

        self.is_speaking = True
        print(f"[EXECUTING] {step.get('embodiment')}")

        await self.expr.execute(agent_type=self.agent, embodiment=step["embodiment"], packet=self.expr.build(step))

        self.is_speaking = False

    """Handles user navigation commands like continue, repeat step, repeat section, and summary"""
    async def handle_navigation(self, expr, agent, step):
        self.state = "NAVIGATION"
        self.last_transcript = None

        await self.say_text(expr, "Would you like to continue, repeat the step, repeat the section, or hear a summary?")

        await self.prepare_for_input(agent)

        timeout = 0
        clarification_used = False

        while timeout < 80:

            if self.is_speaking:
                await asyncio.sleep(0.1)
                continue

            if self.interrupted:
                self.interrupted = False
                await self.say_text(expr, "Paused. Continue when ready.")
                await self.set_led("listening")
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

                await self.say_text(expr, "Sorry, I didn't understand. Please say continue, repeat, section, or summary.")

                await self.prepare_for_input(agent)

                continue

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

        await self.prepare_for_input(agent)

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

                await self.prepare_for_input(agent)

                timeout = 0
                continue

            transcript = agent.state.latest_transcript

            if not transcript:
                await asyncio.sleep(0.1)
                timeout += 1

                if timeout >= 80:
                    retries_used += 1

                    if retries_used == 1:
                        await self.say_text(expr, "I didn't hear a response. Please say Option A, Option B, or Option C.")

                        await self.prepare_for_input(agent)

                        timeout = 0
                        continue

                    await self.say_text(expr, feedback.get("incorrect", f"Sorry, the correct answer is Option {correct_answer.upper()}."))

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

                if retries_used == 1:
                    await self.say_text(expr, "I'm sorry, I didn't catch that. Please say Option A, Option B, or Option C.")

                    await self.prepare_for_input(agent)

                    continue

                await self.say_text(expr, feedback.get("incorrect", f"Sorry, the correct answer is Option {correct_answer.upper()}."))

                return "incorrect"

            if detected == correct_answer:

                await self.say_text(expr, feedback.get("correct", "Correct."))

                return "correct"

            await self.say_text(expr, feedback.get("incorrect", f"Sorry, the correct answer is Option {correct_answer.upper()}."))

            return "incorrect"

    """Creates a clean way of determining correct answers based on the user input."""
    def parse_answer(self, text):
        if not text:
            return None

        text = re.sub(r"[^a-z\s]", "", text.lower().strip())

        tokens = text.split()

        for t in tokens:
            if t in ["a", "b", "c"]:
                return t
            if t in ["bee", "be"]:
                return "b"
            if t in ["sea", "see"]:
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

    """Plays the current section summary if the user wants a quick overview."""
    async def play_summary(self, step, expr):
        current_section = step.get("section")

        summary_text = None

        for s in self.steps:
            if s.get("section") != current_section:
                continue

            summary = s.get("summary")

            if not summary:
                continue

            if isinstance(summary, dict):
                if not summary.get("enabled", False):
                    continue

                summary_text = summary.get("text")

            else:
                summary_text = str(summary)

            if summary_text:
                break

        if not summary_text:
            await self.say_text(expr, "No summary available for this section.")
            return

        await self.say_text(expr, summary_text)

    """Speak function used in the above navigation and knowledge checks. Only for hardcoded questions. Expression module still handles the steps."""
    async def say_text(self, expr, text):
        text = text or ""

        await self.set_led("off") # Set the LED off it is the robot's turn to speak
        
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

    """Helper to find the start of section if asked to repeat it."""
    def find_section_start(self, section):
        for i, step in enumerate(self.steps):
            if step.get("section") == section:
                return i
        return 0

    """Function to map the LEDs as requested. Creates a turn using the current state that is send through the expression module."""
    async def set_led(self, state):
        print(f"[LED] {self.led_state} -> {state}")

        if state == self.led_state:     # If the new state is the same as the current one do nothing
            return

        self.led_state = state

        color_map = {
            "listening": "#00FF00",
            "freeze": "#66A5ED",
            "processing": "#FFFF00",
            "off": "#000000"
        }

        color = color_map.get(state)

        turn = {
            "embodiment": "trainer",
            "verbal": {"text": ""},
            "nonverbals": [{
                "channel": "led",
                "action": "on" if color else "off",
                **({"color": color} if color else {})
            }]
        }

        await self.expr.execute(
            agent_type=self.agent,
            embodiment="trainer",
            packet=self.expr.build(turn)
        )