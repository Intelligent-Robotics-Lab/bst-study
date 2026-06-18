from dataclasses import dataclass
from logic.dtt_module.models.enums import CurrentState, TrialState

@dataclass
class StateSnapshot:
    state: CurrentState
    trial_state: TrialState
    trial_sd: str | None
    current_sd: str | None