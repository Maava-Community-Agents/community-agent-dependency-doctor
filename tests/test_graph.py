import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import graph


class FakeGateway:
    def __init__(self):
        self.agents = []

    def chat(self, message, *, system=None, agent="main", session=None):
        self.agents.append(agent)
        return f"{agent} done"


def test_team_runs_every_sub_agent_in_order():
    gw = FakeGateway()
    assert graph.run_team("hello", gw) == "reviewer done"
    assert gw.agents == list(graph.STEPS)
