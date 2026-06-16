import asyncio
import json
import re
import time
from expression_module.expression_module import ExpressionModule
from perception.perception_client import PerceptionClient
from perception.sample_interaction import SampleInteractionAgent

class BaseInteraction:
    """Base class for instructional interactions.

    Provides shared functionality for perception handling, navigation, knowledge checks, LED control, 
    speech output, and freeze-state management."""

    def __init__(self, agent=None):
        """Initializes shared interaction state, perception tracking,
        speech control flags, LED status, and gesture-detection timers."""
        self.agent = agent
        self.state = "IDLE"
        self.is_speaking = False
        self.interrupted = False
        self.current_index = 0
        self.current_section = None
        self.last_transcript = None
        self.steps = []
        self.WAKE_WORDS = {"freeze", "free", "breeze"}
        self.expr = ExpressionModule()
        self.accepting_input = True
        self.led_state = None
        self.one_hand_up_start_time = None
        self.one_hand_up_active = False
        self.HAND_HOLD_THRESHOLD = 3.0
        self.hand_last_seen_time = 0
        self.hand_lost_timeout = 0.5

    def load_steps(self):
        raise NotImplementedError

    def get_module_name(self):
        return "base"

    async def run_main_loop(self, agent):
        raise NotImplementedError

    async def execute(self):
        """Initializes the interaction environment, starts perception processing, 
        and runs the module's main instructional loop."""
        
        print(f"\n[{self.get_module_name().upper()}] Starting module...")
        self.steps = self.load_steps()

        # NOTE: future addition to set both robots to attend to neutral when the process is started.

        agent = SampleInteractionAgent(silence_timeout=2.0) # Two-second timeout to gather final transcript
        client = PerceptionClient(server_host="141.210.88.210", server_port=8000)

        task = asyncio.create_task(self.run_perception(client, agent))

        try:
            await self.run_main_loop(agent)
        finally:
            task.cancel()

        print(f"\n[{self.get_module_name().upper()} COMPLETE]")

    # -------------------------
    # PERCEPTION HANDLING TASKS
    # -------------------------

    async def run_perception(self, client, agent):
        """Continuously receives perception events and routes emotion, speech, 
        and gesture updates to their appropriate handlers."""

        async for event in client.events():

            event_type = event.get("event_type")
            payload = event.get("payload", {})

            # DEBUG RAW STREAM (optional but useful)
            # print(f"[PERCEPTION] {event_type}")

            if event_type == "emotion_update":
                agent.handle_emotion(payload)

            elif event_type == "asr_update":
                await self.handle_asr(payload, agent)

            elif event_type == "gesture_update":
                action = self.process_gesture(payload)

                if action == "freeze":
                    print("[PERCEPTION] FREEZE TRIGGERED (one_hand_up)")
                    await self.trigger_freeze()

    async def handle_asr(self, payload, agent):
        """Processes speech recognition results, detects wake words (now the backup to hand-raise),
        and forwards valid user transcripts to the interaction agent."""

        transcript = (payload.get("transcript") or "").lower().strip()
        cleaned = re.sub(r"[^\w\s]", "", transcript) # Remove any puncutation to detect wake-word more robustly

        if transcript:
            print(f"[ASR] {transcript}")

        tokens = cleaned.split()

        # Trigger a freeze if any of the WAKE WORDS are detected
        if any(word in tokens for word in self.WAKE_WORDS):
            await self.trigger_freeze()
            return

        if self.is_speaking or not self.accepting_input:
            return

        agent.handle_asr(payload)

    def process_gesture(self, payload):
        """Processes gesture perception data and converts it into high-level 
        interaction events such as freeze requests."""

        pred = payload.get("prediction", {})
        meta = pred.get("meta", {})
        motion = pred.get("motion", {})

        # Optional DEBUG statement if necessary
        # self.debug_gesture(payload)

        now = time.time()

        # Robust statement to detect hand-raise as it is allowed to grab from multiple backend parameters
        is_up = (meta.get("one_hand_up", False) or meta.get("left_hand_up", False) or meta.get("right_hand_up", False))

        # If gesture is seen, update the "last_seen_time"
        if is_up:
            self.hand_last_seen_time = now

            # Begin timing if not already going
            if self.one_hand_up_start_time is None:
                self.one_hand_up_start_time = now

            held = now - self.one_hand_up_start_time

            # Trigger freeze once the threshold has been passed (3 seconds)
            if held >= self.HAND_HOLD_THRESHOLD and not self.one_hand_up_active:
                self.one_hand_up_active = True
                print("[GESTURE] one_hand_up HELD -> FREEZE")
                return "freeze"

        else:
            # Reset if gesture disappears for the threshold (0.5 seconds)
            if now - self.hand_last_seen_time > self.hand_lost_timeout:
                self.one_hand_up_start_time = None
                self.one_hand_up_active = False

        return None

    def debug_gesture(self, payload):

        pred = payload.get("prediction", {})
        motion = pred.get("motion", {})
        meta = pred.get("meta", {})

        print(
            f"[GESTURE DEBUG] "
            f"one_hand_up(meta)={meta.get('one_hand_up')} "
            f"left={meta.get('left_hand_up')} "
            f"right={meta.get('right_hand_up')} "
            f"counter={motion.get('one_hand_up_counter')} "
            f"last_action={pred.get('last_action')}"
        )

    async def wait_for_transcript(self, agent, timeout=80):
        """Waits for a user transcript while respecting speaking and
        interruption states. Returns the transcript or None on timeout."""

        elapsed = 0

        while elapsed < timeout: # Approximately 8 seconds

            if self.is_speaking:
                await asyncio.sleep(0.1)
                continue

            if self.interrupted:
                await asyncio.sleep(0.1)
                continue

            transcript = agent.state.latest_transcript

            if transcript:
                text = transcript.lower().strip() # Clean the transcript
                agent.state.latest_transcript = None # Reset the transcript
                return text

            await asyncio.sleep(0.1)
            elapsed += 1

        return None
    
    async def wait_for_any_response(self, agent):

        print("[WAITING FOR RESPONSE]")

        agent.state.latest_transcript = None
        self.last_transcript = None

        await self.prepare_for_input(agent)

        retries_used = 0
        timeout = 0

        while True:
            # User raised hand to pause the interaction
            if self.interrupted:
                return None

            transcript = agent.state.latest_transcript

            if transcript:
                print(f"[FOUND TRANSCRIPT] {transcript}")

                text = transcript.lower().strip()

                self.last_transcript = text
                agent.state.latest_transcript = None

                await self.set_led("off")

                return text

            await asyncio.sleep(0.1)
            timeout += 1

            if timeout >= 60:  # Only a 6-second timeout for the tutorial phase as we expect faster answers

                retries_used += 1

                # Only allow 2 retries before moving on
                if retries_used < 2:
                    await self.say_text(
                        self.expr,
                        "Sorry, I didn't hear a response. Please try again."
                    )

                    await self.prepare_for_input(agent)
                    timeout = 0
                    continue

                await self.say_text(
                    self.expr,
                    "Sorry, I still didn't hear a response. We will continue."
                )

                await self.set_led("off")
                return None
    
    # --------------------
    # NAVIGATION FUNCTIONS
    # --------------------

    async def handle_navigation(self, expr, agent, step):
        """Processes navigation commands during instructional content,
        including continue, repeat, section replay, and summary requests."""

        self.state = "NAVIGATION"
        self.last_transcript = None

        await self.say_text(expr, "Please say, continue, repeat the section, repeat the statement, or summary?")
        await self.prepare_for_input(agent)

        timeout = 0
        clarification_used = False

        while timeout < 80: # Approximately an 8-second timeout

            if self.is_speaking:
                await asyncio.sleep(0.1)
                continue

            # Remind user they are arleady paused if freeze command comes again
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
                await self.say_text(expr, "Continuing.")
                self.state = "LECTURE"
                return "continue"

            if "summary" in text:
                await self.say_text(expr, "Here is a summary.")
                self.state = "LECTURE"
                return "summary"

            if "section" in text:
                await self.say_text(expr, "Repeating that section.")
                self.state = "LECTURE"
                return "repeat_section"

            if "repeat" in text or "again" in text:
                await self.say_text(expr, "Repeating that statement.")
                self.state = "LECTURE"
                return "repeat_step"

            # Only allow for clarification once, 2 total attempts before moving on
            if not clarification_used:
                clarification_used = True
                await self.say_text(expr, "Sorry, I didn't understand. Please say continue, repeat, section, or summary.")
                await self.prepare_for_input(agent)
                continue

            await self.say_text(expr, "I wasn't able to understand your response, so I will continue. If you wanted something else, please raise your hand and ask again.")
            return "continue"
        
        await self.say_text(
            expr,
            "Sorry, I didn't hear a response. I will continue. If you need anything else, please raise your hand to pause again."
        )
        self.state = "LECTURE"
        return "continue"
        
    async def handle_question_navigation(self, expr, agent, step, full_question):
        """Processes navigation commands while a knowledge check is paused,
        including question replay, section replay, summaries, and continuation."""

        await self.say_text(expr, "Say, repeat the question, repeat the section, summary, or continue?")
        await self.prepare_for_input(agent)

        clarification_used = False
        timeout = 0

        while timeout < 80: # Approximately 8 seconds as before

            # If the users pause while already frozen
            if self.interrupted:
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

            # Prevent duplicate processing
            if text == self.last_transcript:
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

            # Only allow 2 attempts before moving on and requiring the user to pause again if necessary
            if not clarification_used:
                clarification_used = True
                await self.say_text(expr, "Sorry, I didn't understand. Please say repeat question, repeat section, summary, or continue.")
                await self.prepare_for_input(agent)
                timeout = 0
                continue

            await self.say_text(expr, "Sorry, I still didn't understand. I will repeat the question. If that is not what you wanted, please raise your hand for a pause again.")

            return "repeat_question"

        await self.say_text(expr, "Sorry, I didn't hear a response. I will repeat the question. If that is not what you wanted, please raise your hand and we can pause again.")

        return "repeat_question"
    
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

    def find_section_start(self, section):

        for i, step in enumerate(self.steps):
            if step.get("section") == section:
                return i
            
        return 0
    
    # ---------------
    # KNOWLEDGE CHECK
    # ---------------

    async def handle_knowledge_check(self, step, expr, agent):
        """Presents a knowledge check question, evaluates responses,
        manages retries, and provides appropriate feedback."""

        question = step.get("question", {})
        feedback = step.get("feedback", {})

        # Normalize so we worry about only a few cases
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

        # If the robot is speaking continue to wait
        while True:
            if self.is_speaking:
                await asyncio.sleep(0.1)
                continue

            # Interruption handling
            if self.interrupted:
                self.interrupted = False

                action = await self.handle_question_navigation(expr, agent, step, full_question)

                if action == "repeat_question":
                    await self.say_text(expr, "Repeating the question.")
                    await self.say_text(expr, full_question)
                    await self.prepare_for_input(agent)
                    timeout = 0
                    retries_used = 0
                    continue

                if action == "repeat_section":
                    await self.say_text(expr, "Repeating the section.")
                    return "repeat_section"

                if action == "summary":
                    await self.say_text(expr, "Here is a summary.")
                    await self.play_summary(step, expr)
                    await self.say_text(expr, "Now, please answer Option 1, Option 2, Option 3, or say repeat.")
                    await self.prepare_for_input(agent)
                    timeout = 0
                    continue

                # Explicitly ask the user for an answer again after continue to prevent confusion
                if action == "continue":
                    await self.say_text(
                        expr,
                        "Please answer by saying Option 1, Option 2, Option 3, or say Repeat."
                    )
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

                    # Again only allow 2 retries before we move on
                    if retries_used < 2:
                        await self.say_text(
                            expr,
                            "Sorry, I didn't hear a response. Please answer by saying Option 1, Option 2, Option 3, or say Repeat."
                        )
                        await self.prepare_for_input(agent)
                        timeout = 0
                        continue

                    await self.say_text(
                        expr,
                        f"Sorry, I wasn't able to hear a response. To save time, we will move on. The correct answer was option {correct_answer}."
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

            # If repeat is asked for when waiting for a question answer
            if "repeat" in text or "again" in text:
                retries_used = 0
                await self.say_text(expr, full_question)
                await self.prepare_for_input(agent)
                continue

            # Continue is not a valid answer during a knowledge check
            if "continue" in text:
                await self.say_text(
                    expr,
                    "Please answer by saying Option 1, Option 2, Option 3, or say Repeat."
                )

                await self.prepare_for_input(agent)
                continue

            selected = self.normalize_answer(text)

            if selected is None:
                retries_used += 1

                # Only proceed if the 2nd retry hasn't been done
                if retries_used < 2:
                    await self.say_text(
                        expr,
                        "I didn't understand that. Please answer by saying Option 1, Option 2, Option 3, or say Repeat."
                    )
                    await self.prepare_for_input(agent)
                    continue

                await self.say_text(
                    expr,
                    f"Sorry, I wasn't able to get a response. To save time we will go on. The correct answer was option {correct_answer}."
                )
                return "invalid"

            # Check for correctness of a 2nd response
            correct_answer = self.normalize_answer(
                str(question.get("correct_answer") or "")
            )

            # Handle correct reponse
            if selected == correct_answer:
                await self.flash_correct_led()
                await self.say_text(expr, feedback.get("correct", "Correct."))
                return "correct"

            # Incorrect response handling
            await self.say_text(
                expr,
                feedback.get(
                    "incorrect",
                    f"Sorry, the correct answer is option {correct_answer}."
                )
            )
            return "incorrect"

    def normalize_answer(self, text: str):
        """Converts recognized answer variations into a standardized response
        format for knowledge check evaluation."""

        text = text.lower()

        if any(x in text for x in ["1", "one", "first", "option one", "option 1"]):
            return "1"
        if any(x in text for x in ["2", "two", "to", "too", "second", "option two", "option 2"]):
            return "2"
        if any(x in text for x in ["3", "three", "third", "option three", "option 3"]):
            return "3"

        return None

    def is_correct_answer(self, text, accepted_answers):

        text = text.lower().strip()

        for answer in accepted_answers:
            if answer.lower().strip() in text:
                return True

        return False

    async def flash_correct_led(self):
        await self.set_led("orange")
        await asyncio.sleep(1)

    # ------------------------
    # ROBOT-SPECIFIC UTILITIES
    # ------------------------

    async def say_text(self, expr, text):

        text = text or ""

        await self.set_led("off") # Always set the LED off it is the robot's turn to speak
        
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

    async def execute_step(self, step):
        """Executes a single instructional step through the expression module
        and manages speaking state transitions."""

        if not step.get("embodiment"):
            return
        
        # Turn the LED off at the start of each step indicating it is the robot's turn to speak
        await self.set_led("off")

        self.is_speaking = True
        print(f"[EXECUTING] {step.get('embodiment')}")

        await self.expr.execute(agent_type=self.agent, embodiment=step["embodiment"], packet=self.expr.build(step))

        self.is_speaking = False

    async def set_led(self, state):
        """Updates the robot's LED state and sends the corresponding
        visual feedback command through the expression module."""

        print(f"[LED] {self.led_state} -> {state}")

        # If the new state is the same as the current one do nothing
        if state == self.led_state:
            return

        self.led_state = state

        # Map the used colors to implementable hex values
        color_map = {
            "green": "#00FF00",
            "blue": "#0000FF",
            "yellow": "#FFBB00",
            "orange": "#FF6F00",
            "red": "#FF0000",
            "off": "#000000"
        }

        color = color_map.get(state)

        # Create a turn that can be executed by Furhat out of the inputs
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

    async def signal_listening(self):
        await self.set_led("green")

    async def trigger_freeze(self):

        self.interrupted = True

        # Reset gesture states to prevent freeze from looping
        self.one_hand_up_start_time = None
        self.one_hand_up_active = False

        # Stays blue until the trainer asks you how to proceed
        await self.set_led("blue")

    async def prepare_for_input(self, agent, delay=0.5):
        """Prepares the system to receive user input by clearing transcript
        buffers, updating LEDs, and enabling input processing. Written to reduce copy-and-paste code."""

        self.accepting_input = False

        await asyncio.sleep(delay)

        agent.state.latest_transcript = None
        self.last_transcript = None

        await self.set_led("green")

        self.accepting_input = True

    # -------------------
    # TUTORIAL ACTIVITIES
    # -------------------

    async def handle_led_demo(self, step):
        await self.execute_step(step)
        await self.set_led(step.get("led"))
        await asyncio.sleep(2)
        await self.set_led("off")

    async def handle_interaction(self, step, agent):
        """Executes a tutorial interaction exercise depending on the content."""

        mode = step.get("mode")

        await self.execute_step(step)

        if mode == "pause":
            await self.prepare_for_input(agent)

            while not self.interrupted:
                await asyncio.sleep(0.1)

            await asyncio.sleep(2)

            self.interrupted = False

            await self.set_led("off")

            await self.say_text(
                self.expr,
                "Great! I detected your raised hand and paused the interaction."
            )

            return

        # Everything else waits for a response
        response = await self.wait_for_any_response(agent)

        # Pause request occured while waiting for a response
        if self.interrupted:
            return
        
        # Timed out twice and moved on
        if response is None:
            return

        if mode == "response":

            reply = step.get(
                "success_text",
                "Great! Thank you for sharing!"
            )

            await self.say_text(self.expr, reply)

        elif mode == "question":

            await self.say_text(
                self.expr,
                "Thanks for asking! For this tutorial, my favorite color is blue."
            )

        elif mode == "feedback":

            color = step.get("feedback_led", "yellow")
            duration = step.get("feedback_duration", 2)

            await self.set_led(color)

            await asyncio.sleep(duration)

            await self.set_led("off")

            await self.say_text(
                self.expr,
                "Great! While the LEDs were briefly yellow, I was demonstrating feedback processing."
            )

        elif mode == "red_demo":

            await self.set_led("red")

            await asyncio.sleep(2)

            await self.set_led("off")

            await self.say_text(
                self.expr,
                "The red LEDs indicate that I was unable to understand the response. During this study, you may occasionally see this signal or be asked to repeat what you said. Your patience is much appreciated."
            )