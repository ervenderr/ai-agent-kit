import pytest

from app.agent.caps import CapExceeded, Caps
from app.agent.state import RunState


def state(**kw) -> RunState:
    s = RunState("r", 1)
    for k, v in kw.items():
        setattr(s, k, v)
    return s


@pytest.mark.parametrize(
    ("kw", "pending", "kind"),
    [
        ({"steps": 8}, 0, "steps"),
        ({"tool_calls": 9}, 2, "tool_calls"),
        ({"input_tokens": 300_000}, 0, "input_tokens"),
        ({"cost": 1.0}, 0, "cost"),
    ],
)
def test_cap_raises(kw, pending, kind):
    with pytest.raises(CapExceeded) as e:
        Caps().check(state(**kw), pending)
    assert e.value.kind == kind


def test_seconds_cap():
    s = state()
    s.started -= 120
    with pytest.raises(CapExceeded, match="seconds"):
        Caps().check(s)


def test_under_caps_passes():
    Caps().check(state(steps=7, tool_calls=8), 2)
