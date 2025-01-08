from questionpy import Attempt, BaseAttemptState, BaseScoringState


class MyAttempt(Attempt):
    formulation = ""

    def _compute_score(self) -> float:
        return 1

    # These are forward references, i.e. the types don't exist yet. get_mro_type_hint will support this, as long as it's
    # called after the types are defined, so it must be called after module execution. We test that we call
    # get_type_hints correctly.
    attempt_state: "MyAttemptState"
    scoring_state: "MyScoringState"


class MyAttemptState(BaseAttemptState):
    pass


class MyScoringState(BaseScoringState):
    pass


def test_should_resolve_forward_references() -> None:
    assert MyAttempt.attempt_state_class is MyAttemptState
    assert MyAttempt.scoring_state_class is MyScoringState
