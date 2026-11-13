"""The agent's team: planner -> researcher -> writer -> reviewer, wired as a LangGraph graph.

Every node is a sub-agent: the agent's own ``instructions.md`` plus that sub-agent's brief from
``sub_agents/<name>/instructions.md``, run on a maava gateway. If langgraph isn't installed the
same steps run in order, so the agent still works.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, TypedDict

from maava_agent import Agent

ROOT = Path(__file__).resolve().parent.parent
STEPS = ("planner", "researcher", "writer", "reviewer")


class State(TypedDict, total=False):
    request: str
    planner: str
    researcher: str
    writer: str
    reviewer: str


def sub_agent(name: str, gateway=None) -> Agent:
    brief = (ROOT / "instructions.md").read_text() + "\n\n" + (ROOT / "sub_agents" / name / "instructions.md").read_text()
    return Agent(brief, gateway=gateway, agent_id=name)


def _message(name: str, state: State) -> str:
    parts = [f"Request:\n{state['request']}"]
    parts += [f"{s.capitalize()} output:\n{state[s]}" for s in STEPS[: STEPS.index(name)] if state.get(s)]
    return "\n\n".join(parts)


def _nodes(gateway=None) -> dict[str, Callable[[State], State]]:
    def make(name: str):
        agent = sub_agent(name, gateway)
        return lambda state: {name: agent.run(_message(name, state))}

    return {name: make(name) for name in STEPS}


def build(gateway=None):
    """The compiled LangGraph graph, or ``None`` if langgraph isn't installed."""
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        return None
    graph = StateGraph(State)
    for name, node in _nodes(gateway).items():
        graph.add_node(name, node)
    graph.add_edge(START, STEPS[0])
    for a, b in zip(STEPS, STEPS[1:]):
        graph.add_edge(a, b)
    graph.add_edge(STEPS[-1], END)
    return graph.compile()


def run_team(request: str, gateway=None) -> str:
    graph = build(gateway)
    if graph is not None:
        return graph.invoke({"request": request})["reviewer"]
    state: State = {"request": request}
    for name, node in _nodes(gateway).items():
        state.update(node(state))
    return state["reviewer"]
