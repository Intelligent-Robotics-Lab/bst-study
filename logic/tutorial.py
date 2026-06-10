import json
import asyncio
from logic.base_interaction import BaseInteraction

class Tutorial(BaseInteraction):
    """Implements the tutorial phase of the study.

    Guides participants through practice interactions,
    LED demonstrations, pause gestures, and example
    responses before the main instructional modules begin."""
    
    # MODULE DATA

    def get_module_name(self):
        return "tutorial"

    def load_steps(self):
        with open("data/tutorial_data.json", "r") as f:
            return json.load(f)["steps"]

    # MAIN EXECUTION LOOP

    async def run_main_loop(self, agent):
        """Executes the tutorial sequence. Iterates through the steps
        and routes to the appropriate interactions."""

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