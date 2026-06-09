import json
import asyncio
from logic.base_interaction import BaseInteraction

class Tutorial(BaseInteraction):

    def get_module_name(self):
        return "tutorial"

    def load_steps(self):
        with open("data/tutorial_data.json", "r") as f:
            return json.load(f)["steps"]

    async def wait_for_any_response(self, agent):
        print("[WAITING FOR RESPONSE]")

        agent.state.latest_transcript = None
        self.last_transcript = None

        await self.prepare_for_input(agent)   # turns green on

        while True:
            transcript = agent.state.latest_transcript

            if transcript:
                print(f"[FOUND TRANSCRIPT] {transcript}")

                text = transcript.lower().strip()

                self.last_transcript = text
                agent.state.latest_transcript = None

                await self.set_led("off") # When response received, stop listening

                return text

            await asyncio.sleep(0.1)

    async def run_main_loop(self, agent):
        while self.current_index < len(self.steps):

            step = self.steps[self.current_index]
            self.current_section = step.get("section")
            step_type = step.get("type")

            print(f"\n[INDEX] {self.current_index}")
            print(f"[SECTION] {self.current_section}")
            print(f"[TYPE] {step_type}")

            if step_type == "led_demo":
                await self.handle_led_demo(step)

            elif step_type == "interaction":
                await self.handle_interaction(step, agent)

            else:
                await self.execute_step(step)

                if self.interrupted:
                    self.interrupted = False

                    action = await self.handle_navigation(self.expr, agent, step)

                    if action == "repeat_step":
                        continue

                    if action == "repeat_section":
                        self.current_index = self.find_section_start(self.current_section)
                        continue

            self.current_index += 1

    """Will describe what the LED does and then flash the color for 2 seconds to the user."""
    async def handle_led_demo(self, step):
        await self.execute_step(step)

        await self.set_led(step.get("led"))

        await asyncio.sleep(2)

        await self.set_led("off")

    async def handle_interaction(self, step, agent):
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