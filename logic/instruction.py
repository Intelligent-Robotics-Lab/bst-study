import json
from logic.base_interaction import BaseInteraction
from logic.monitor import update_monitor

SECTION_TO_PHASE = {
    "instruction_intro": 1,
    "skills_overview": 2,
    "prompting_error_correction": 3,
    "reinforcement_motivation": 4,
    "full_process_walkthrough": 5,
}

class Instruction(BaseInteraction):
    """Implements the instruction phase of the study.

    Loads instruction content from JSON and uses the shared
    interaction functionality provided by BaseInteraction."""
    
    # MODULE DATA

    def get_module_name(self):
        return "instruction"

    def load_steps(self):
        with open("data/test_data.json", "r") as f:
            return json.load(f)["steps"]

    # MAIN EXECUTE

    async def run_main_loop(self, agent):
        """Executes the primary module flow by iterating through all
        instructional steps, handling knowledge checks, navigation
        requests, and section replay behavior."""

        # Debug for sync client
        print(f"[Instruction] sync id = {id(self.sync)}")
        print(f"[Instruction] session id = {self.study_config['session_id']}")

        update_monitor(screen="instruction", current_phase=1)
        await self.set_attention("kid", "down")

        last_phase = None
        while self.current_index < len(self.steps):

            step = self.steps[self.current_index]
            step_type = step.get("type")
            self.current_section = step.get("section")

            phase = SECTION_TO_PHASE.get(self.current_section, 1)

            # Only update webpage when phase changes
            if phase != last_phase:
                update_monitor(screen="instruction", current_phase=phase)
                last_phase = phase

            print(f"\n[INDEX] {self.current_index}")
            print(f"[SECTION] {self.current_section}")
            print(f"[PHASE] {phase}")
            print(f"[TYPE] {step.get('type')}")
            print(f"[SPEAKING] {self.is_speaking}")

            # Knowledge checks are handled seperately from standard content steps
            if step_type == "knowledge_check":
                result = await self.handle_knowledge_check(step, self.expr, agent)

                if result == "repeat_section":
                    self.current_index = self.find_section_start(self.current_section)
                    continue

                self.current_index += 1
                continue

            await self.execute_step(step)

            # If user requested a pause via hand-raise
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

        # Instruction module finished
        update_monitor(screen="modeling", current_phase=1)