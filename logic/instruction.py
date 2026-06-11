import json
from logic.base_interaction import BaseInteraction
from logic.monitor import update_monitor

SECTION_TO_PHASE = {
    "intro": 1,
    "instruction_intro": 2,
    "skills_overview": 3,
    "prompting_error_correction": 4,
    "reinforcement_motivation": 5,
    "full_process_walkthrough": 6,
    "checkpoint": 6
}


"""This class contains all of the logic for navigating through the instruction module."""
class Instruction(BaseInteraction):

    # Module name used for logic and runtime identification
    def get_module_name(self):
        return "instruction"

    # Loads instruction phase steps from the JSON data
    def load_steps(self):
        with open("data/instruction_data.json", "r") as f:
            return json.load(f)["steps"]

    async def run_main_loop(self, agent):

        update_monitor(
            screen="instruction",
            current_phase=1
        )

        last_phase = None

        while self.current_index < len(self.steps):

            step = self.steps[self.current_index]
            self.current_section = step.get("section")

            phase = SECTION_TO_PHASE.get(
                self.current_section,
                1
            )

            # Only update webpage when phase changes
            if phase != last_phase:

                update_monitor(
                    screen="instruction",
                    current_phase=phase
                )

                last_phase = phase

            print(f"\n[INDEX] {self.current_index}")
            print(f"[SECTION] {self.current_section}")
            print(f"[PHASE] {phase}")
            print(f"[TYPE] {step.get('type')}")
            print(f"[SPEAKING] {self.is_speaking}")

            if step.get("type") == "knowledge_check":

                result = await self.handle_knowledge_check(
                    step,
                    self.expr,
                    agent
                )

                if result == "repeat_section":
                    self.current_index = self.find_section_start(
                        self.current_section
                    )
                    continue

                self.current_index += 1
                continue

            await self.execute_step(step)

            if self.interrupted:

                self.interrupted = False

                action = await self.handle_navigation(
                    self.expr,
                    agent,
                    step
                )

                if action == "repeat_step":
                    continue

                if action == "repeat_section":
                    self.current_index = self.find_section_start(
                        self.current_section
                    )
                    continue

                if action == "summary":
                    await self.play_summary(
                        step,
                        self.expr
                    )
                    continue

            self.current_index += 1

        # Instruction module finished
        update_monitor(
            screen="modeling",
            current_phase=1
        )