import json
from logic.base_interaction import BaseInteraction
from logic.monitor import update_monitor

SECTION_TO_PHASE = {
    "manding": 1,
    "imitative": 2,
    "receptive": 3,
    "tacting": 4,
    "emotion": 5
}


class Modeling(BaseInteraction):

    def get_module_name(self):
        return "modeling"

    def load_steps(self):
        with open("data/modeling_data.json", "r") as f:
            return json.load(f)["steps"]

    async def run_main_loop(self, agent):

        print(">>> MODELING MAIN LOOP STARTED <<<")

        update_monitor(
            screen="modeling",
            current_phase=0
        )
        print("MONITOR SET TO MODELING")
        last_phase = None

        while self.current_index < len(self.steps):

            step = self.steps[self.current_index]
            self.current_section = step.get("section")

            phase = SECTION_TO_PHASE.get(
                self.current_section
            )

            if phase is not None and phase != last_phase:

                update_monitor(
                    screen="modeling",
                    current_phase=phase
                )

                last_phase = phase

            print(f"\n[INDEX] {self.current_index}/{len(self.steps)}")
            print(f"[SECTION] {self.current_section}")
            print(f"[PHASE] {phase}")
            print(f"[TYPE] {step.get('type')}")

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

        update_monitor(
            screen="rehearsal",
            current_phase=0
        )