"""Builds the LangGraph: Requirements -> Design -> Developer -> Testing -> Security,
with an approval gate after every stage and repair loops back to Developer."""
from langgraph.graph import END, START, StateGraph

from .gates import make_gate_node, make_request_node, route_after_gate
from .nodes.design_node import DESIGN
from .nodes.developer_node import DEVELOPER
from .nodes.requirements_node import REQUIREMENTS
from .nodes.security_node import SECURITY
from .nodes.stage_wrapper import make_stage_node
from .nodes.testing_node import TESTING
from .routing import route_after_stage
from .state import NEXT, RunState

SPECS = [REQUIREMENTS, DESIGN, DEVELOPER, TESTING, SECURITY]


def build_graph(tools, settings, checkpointer):
    g = StateGraph(RunState)

    for spec in SPECS:
        s = spec.name
        g.add_node(s, make_stage_node(spec, tools, settings))
        g.add_node(f"request_{s}", make_request_node(s, tools, settings))
        g.add_node(f"gate_{s}", make_gate_node(s, settings))

    g.add_edge(START, "requirements")

    for spec in SPECS:
        s = spec.name
        stage_routes = {"halt": END, "request": f"request_{s}"}
        if spec.repairable:
            stage_routes["repair"] = "developer"   # testing / security failures go back to Developer
        g.add_conditional_edges(s, route_after_stage, stage_routes)

        g.add_edge(f"request_{s}", f"gate_{s}")

        gate_routes = {"same": s, "done": END}
        if s in NEXT:
            gate_routes["next"] = NEXT[s]
        g.add_conditional_edges(f"gate_{s}", route_after_gate(s), gate_routes)

    return g.compile(checkpointer=checkpointer)
