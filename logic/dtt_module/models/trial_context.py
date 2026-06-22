from dataclasses import dataclass, field
import time
from logic.dtt_module.models.enums import CurrentState, TrialState

@dataclass
class TrialContext:
    state: CurrentState = CurrentState.USER
    trial_state: TrialState = TrialState.SD

    trial_sd: str | None = None
    current_sd: str | None = None
    latin_square_configuration: int = 1

    reinforcement_source: str | None = None
    last_processed: str | None = None

    completed_sds: set = field(default_factory=set)

    last_activity: float = field(default_factory=time.monotonic)
    prompt_given: bool = False

    session_complete: bool = False