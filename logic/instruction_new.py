import json
from logic.base_interaction import BaseInteraction

"""This class contains all of the logic for navigating through the instruction module."""
class Instruction(BaseInteraction):
    # Module name used for loggic and runtime identification
    def get_module_name(self):
        return "instruction"

    # Loads instruction phase steps from the JSON data
    def load_steps(self):
        with open("data/instruction_data.json", "r") as f:
            return json.load(f)["steps"]

    async def run_main_loop(self, agent):

        while self.current_index < len(self.steps):

            step = self.steps[self.current_index]
            self.current_section = step.get("section")

            print(f"\n[INDEX] {self.current_index}")
            print(f"[SECTION] {self.current_section}")
            print(f"[TYPE] {step.get('type')}")
            print(f"[SPEAKING] {self.is_speaking}")

            if step.get("type") == "knowledge_check":
                result = await self.handle_knowledge_check(step, self.expr, agent)

                if result == "repeat_section":
                    self.current_index = self.find_section_start(self.current_section)
                    continue

                self.current_index += 1
                continue

            await self.execute_step(step)

            if self.interrupted:
                self.interrupted = False

                action = await self.handle_navigation(self.expr, agent, step)

                if action == "repeat_step":
                    continue

                if action == "repeat_section":
                    self.current_index = self.find_section_start(self.current_section)
                    continue

                if action == "summary":
                    await self.play_summary(step, self.expr)
                    continue

            self.current_index += 1