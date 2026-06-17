@dataclass
class TrialContext:
    state: CurrentState
    trial_state: TrialState
    trial_sd: str | None = None
    current_sd: str | None = None
    reinforcement_source: str | None = None
    last_processed: str | None = None
    completed_sds: set[str] = field(default_factory=set)