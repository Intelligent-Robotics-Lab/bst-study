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
        self.WAKE_WORDS = {"freeze", "free", "breeze"} # Removed "tree" and "trees" from here since three is a valid option
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

    """Wait for a response function to be used in the tutorial phase."""
    async def wait_for_transcript(self, agent, timeout=80):
        elapsed = 0

        while elapsed < timeout:

            if self.is_speaking:
                await asyncio.sleep(0.1)
                continue

            if self.interrupted:
                await asyncio.sleep(0.1)
                continue

            transcript = agent.state.latest_transcript

            if transcript:
                text = transcript.lower().strip()
                agent.state.latest_transcript = None
                return text

            await asyncio.sleep(0.1)
            elapsed += 1

        return None

    """Function to clean up redundant code in the following functions."""
    async def prepare_for_input(self, agent, delay=0.5):
        self.accepting_input = False

        await asyncio.sleep(delay)

        agent.state.latest_transcript = None
        self.last_transcript = None

        await self.set_led("green")

        self.accepting_input = True

    """Triggers interrupt state and provides LED feedback to indicate the word was detected."""
    async def trigger_freeze(self):
        self.interrupted = True
        await self.set_led("blue")

    """Function to turn on the green LED when listening"""
    async def signal_listening(self):
        await self.set_led("green")

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

        await self.say_text(expr, "Please say, continue, repeat the step, repeat the section, summary?")

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
                await self.set_led("green")
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

            await self.say_text(expr, "I wasn't able to understand your response, so I will continue. If you wanted something else, please signal to pause and ask again.")
            return "continue"
        
    """Added function to handle freeze requests in question since the responses will be different."""    
    async def handle_question_navigation(self, expr, agent, step, full_question):

        await self.say_text(expr, "Say, repeat the question, repeat the section, summary, or continue?")

        await self.prepare_for_input(agent)

        clarification_used = False
        timeout = 0

        while timeout < 80:

            if self.interrupted: # If the users say freeze again while already paused

                self.interrupted = False

                await self.say_text(expr, "You are already paused. Please say repeat question, repeat section, summary, or continue.")

                await self.prepare_for_input(agent)

                continue

            transcript = agent.state.latest_transcript

            if not transcript:
                await asyncio.sleep(0.1)
                timeout += 1
                continue

            text = transcript.lower().strip()

            if text == self.last_transcript: # Prevents duplicate processing
                await asyncio.sleep(0.1)
                continue

            self.last_transcript = text
            agent.state.latest_transcript = None

            print(f"[QUESTION NAV] {text}")

            if "question" in text:
                return "repeat_question"

            if "section" in text:
                return "repeat_section"

            if "summary" in text:
                return "summary"

            if "continue" in text:
                return "continue"

            if not clarification_used: # This only allows 2 attempts before moving on and requiring the user to pause again if necessary

                clarification_used = True

                await self.say_text(expr, "Sorry, I didn't understand. Please say repeat question, repeat section, summary, or continue.")

                await self.prepare_for_input(agent)

                timeout = 0

                continue

            await self.say_text(expr, "Sorry, I still didn't understand. I will repeat the question. If that is not what you wanted, please say freeze again.")

            return "repeat_question"

        await self.say_text(expr, "Sorry, I didn't hear a response. I will repeat the question. If that is not what you wanted, please say freeze again.")

        return "repeat_question"
    
    async def flash_correct_led(self):
        await self.set_led("orange")
        await asyncio.sleep(1)

    def normalize_answer(self, text: str):
        text = text.lower()

        if any(x in text for x in ["1", "one", "first", "option one", "option 1"]):
            return "1"
        if any(x in text for x in ["2", "two", "to", "too", "second", "option two", "option 2"]):
            return "2"
        if any(x in text for x in ["3", "three", "third", "option three", "option 3"]):
            return "3"

        return None

    async def handle_knowledge_check(self, step, expr, agent):
        question = step.get("question", {})
        feedback = step.get("feedback", {})

        correct_answer = self.normalize_answer(
            str(question.get("correct_answer") or "")
        )

        text = question.get("text", "")
        choices = question.get("choices", [])
        full_question = text + " " + " ".join(choices)

        retries_used = 0
        timeout = 0

        await self.say_text(expr, full_question)
        await self.prepare_for_input(agent)

        while True: # If the robot is speaking continue to wait
            if self.is_speaking:
                await asyncio.sleep(0.1)
                continue

            # Interruption handling
            if self.interrupted:
                self.interrupted = False

                action = await self.handle_question_navigation(expr, agent, step, full_question)

                if action == "repeat_question":
                    await self.say_text(expr, full_question)
                    await self.prepare_for_input(agent)
                    timeout = 0
                    retries_used = 0
                    continue

                if action == "repeat_section":
                    return "repeat_section"

                if action == "summary":
                    await self.play_summary(step, expr)
                    await self.prepare_for_input(agent)
                    timeout = 0
                    continue

                if action == "continue":
                    await self.prepare_for_input(agent)
                    timeout = 0
                    continue

            # Handling the transcripts
            transcript = agent.state.latest_transcript

            if not transcript:
                await asyncio.sleep(0.1)
                timeout += 1

                if timeout >= 80: # Approximately an 8 second timeout
                    retries_used += 1

                    if retries_used < 2:
                        await self.say_text(
                            expr,
                            "Sorry, I didn't hear a response. Please say Option 1, Option 2, Option 3, or say Repeat."
                        )
                        await self.prepare_for_input(agent)
                        timeout = 0
                        continue

                    await self.say_text(
                        expr,
                        f"Sorry, I wasn't able to get a response. To save time, we will move on. The correct answer was option {correct_answer}."
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

            # If repeat command
            if "repeat" in text or "again" in text:
                retries_used = 0
                await self.say_text(expr, full_question)
                await self.prepare_for_input(agent)
                continue

            # Answer normalization
            selected = self.normalize_answer(text)

            if selected is None:
                retries_used += 1

                if retries_used < 2:
                    await self.say_text(
                        expr,
                        "I didn't understand that. Please say Option 1, Option 2, Option 3, or say Repeat."
                    )
                    await self.prepare_for_input(agent)
                    continue

                await self.say_text(
                    expr,
                    f"Sorry, I wasn't able to get a response. To save time we will go on. The correct answer was option {correct_answer}."
                )
                return "invalid"

            # Check for correctness
            correct_answer = self.normalize_answer(
                str(question.get("correct_answer") or "")
            )

            if selected == correct_answer:
                await self.flash_correct_led()
                await self.say_text(expr, feedback.get("correct", "Correct."))
                return "correct"

            # Handling incorrect responses
            await self.say_text(
                expr,
                feedback.get(
                    "incorrect",
                    f"Sorry, the correct answer is option {correct_answer}."
                )
            )
            return "incorrect"

    """Checks whether a transcript matches any accepted answer for the question."""
    def is_correct_answer(self, text, accepted_answers):
        text = text.lower().strip()

        for answer in accepted_answers:
            if answer.lower().strip() in text:
                return True

        return False

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
            "green": "#00FF00",
            "blue": "#0000FF",
            "yellow": "#FFBB00",
            "orange": "#FF8C00",
            "red": "#FF0000",
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

        await self.expr.execute(agent_type=self.agent, embodiment="trainer", packet=self.expr.build(turn))