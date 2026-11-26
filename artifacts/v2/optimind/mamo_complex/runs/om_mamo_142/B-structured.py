# IR: {"sets":{"E":[[1,2],[1,3],[2,3],[2,4],[3,4]],"I":[2,3]},"params":{"cap_1_2":"capacity(1,2)","cap_1_3":"capacity(1,3)","cap_2_3":"capacity(2,3)","cap_2_4":"capacity(2,4)","cap_3_4":"capacity(3,4)"},"variables":{"flow[i,j]":{"index":"E","type":"nonnegative continuous"}},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in E","sum(flow[i,j] for incoming edges to v) = sum(flow[i,j] for outgoing edges from v) for v in I"],"objective":{"sense":"maximize","expression":"flow[1,2] + flow[1,3]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.edges = pyo.Set(
        dimen=2,
        initialize=[(1, 2), (1, 3), (2, 3), (2, 4), (3, 4)],
    )
    model.intermediate_nodes = pyo.Set(initialize=[2, 3])

    capacities = {
        (1, 2): params["cap_1_2"],
        (1, 3): params["cap_1_3"],
        (2, 3): params["cap_2_3"],
        (2, 4): params["cap_2_4"],
        (3, 4): params["cap_3_4"],
    }

    model.capacity = pyo.Param(
        model.edges,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.edges, domain=pyo.NonNegativeReals)

    def capacity_rule(block, tail, head):
        return block.flow[tail, head] <= block.capacity[tail, head]

    model.capacity_limits = pyo.Constraint(
        model.edges, rule=capacity_rule
    )

    def conservation_rule(block, node):
        incoming = sum(
            block.flow[tail, head]
            for tail, head in block.edges
            if head == node
        )
        outgoing = sum(
            block.flow[tail, head]
            for tail, head in block.edges
            if tail == node
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=model.flow[1, 2] + model.flow[1, 3],
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}