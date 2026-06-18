# logic/dtt/commands/command_manager.py

from logic.dtt_module.models.enums import (
    CurrentState,
    TrialState,
    SystemCommand,
)

from logic.dtt_module.models.state_snapshot import (
    StateSnapshot,
)


class CommandManager:

    def __init__(
        self,
        interaction_manager,
    ):
        self.interaction = interaction_manager

    def detect_system_command(
        self,
        transcript: str | None,
    ) -> SystemCommand:

        if not transcript:
            return SystemCommand.NONE

        text = transcript.lower().strip()

        restart_phrases = [
            "restart",
            "start over",
            "reset",
            "restart trial",
        ]

        where_am_i_phrases = [
            "where am i",
            "what do i do",
            "what should i do",
            "what now",
            "what next",
            "help me",
            "what step",
            "what state",
        ]

        if any(
            phrase in text
            for phrase in restart_phrases
        ):
            return SystemCommand.RESTART

        if any(
            phrase in text
            for phrase in where_am_i_phrases
        ):
            return SystemCommand.WHERE_AM_I

        return SystemCommand.NONE

    def build_where_am_i_text(
        self,
        trial_state: TrialState,
        trial_sd: str | None,
    ) -> str:

        mapping = {

            TrialState.SD:
                "You should deliver the discriminative stimulus.",

            TrialState.REINFORCEMENT:
                "You should reinforce the child behavior.",

            TrialState.PROMPTING:
                "You should provide a prompt to the child.",

            TrialState.HP_SD:
                "You should deliver a high probability SD.",

            TrialState.RETRY_SD:
                "You should retry the original SD.",

            TrialState.FEEDBACK:
                "The system is currently giving feedback.",
        }

        base = mapping.get(
            trial_state,
            "You are in the session.",
        )

        if trial_sd:
            base += f" Current target is {trial_sd}."

        return base

    async def handle_system_command(
        self,
        *,
        command: SystemCommand,
        expr,
        feedback,
        current_trial_state,
        current_trial_sd,
    ):

        if command == SystemCommand.RESTART:

            feedback.reset()

            await self.interaction.speak_text(
                expr=expr,
                text="Restarting the current trial.",
            )

            return StateSnapshot(
                state=CurrentState.USER,
                trial_state=TrialState.SD,
                trial_sd=None,
                current_sd=None,
            )

        if command == SystemCommand.WHERE_AM_I:

            explanation = (
                self.build_where_am_i_text(
                    current_trial_state,
                    current_trial_sd,
                )
            )

            await self.interaction.speak_text(
                expr=expr,
                text=explanation,
            )

            return None

        if command == SystemCommand.HELP:

            help_text = (
                "You can say restart, "
                "where am I, help, or stop."
            )

            await self.interaction.speak_text(
                expr=expr,
                text=help_text,
            )

            return None

        if command == SystemCommand.STOP:

            await self.interaction.speak_text(
                expr=expr,
                text="Ending the session.",
            )

            return "STOP"

        return None