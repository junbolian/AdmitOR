# IR: {"sets":{"nodes":[1,2,3,4],"edges":[[1,2],[1,3],[2,3],[2,4],[3,4]],"intermediate":[2,3]},"params":{"cap_1_2":"nonnegative capacity of (1,2)","cap_1_3":"nonnegative capacity of (1,3)","cap_2_3":"nonnegative capacity of (2,3)","cap_2_4":"nonnegative capacity of (2,4)","cap_3_4":"nonnegative capacity of (3,4)"},"variables":{"flow[i,j]":"nonnegative continuous for each edge"},"constraints":["flow[i,j] <= capacity[i,j] for each edge","sum(flow[i,v] for incoming edges) = sum(flow[v,j] for outgoing edges) for v in intermediate"],"objective":"maximize flow[1,2] + flow[1,3]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=[1, 2, 3, 4], ordered=True)
    model.edges = pyo.Set(
        dimen=2,
        initialize=[(1, 2), (1, 3), (2, 3), (2, 4), (3, 4)],
        ordered=True,
    )
    model.intermediate = pyo.Set(initialize=[2, 3], ordered=True)

    capacity_data = {
        (1, 2): params["cap_1_2"],
        (1, 3): params["cap_1_3"],
        (2, 3): params["cap_2_3"],
        (2, 4): params["cap_2_4"],
        (3, 4): params["cap_3_4"],
    }
    model.capacity = pyo.Param(
        model.edges,
        initialize=capacity_data,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.edges, domain=pyo.NonNegativeReals)

    def capacity_rule(block, origin, destination):
        return (
            block.flow[origin, destination]
            <= block.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.edges, rule=capacity_rule
    )

    def conservation_rule(block, node):
        incoming = sum(
            block.flow[origin, destination]
            for origin, destination in block.edges
            if destination == node
        )
        outgoing = sum(
            block.flow[origin, destination]
            for origin, destination in block.edges
            if origin == node
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.intermediate, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=model.flow[1, 2] + model.flow[1, 3],
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this error when no feasible solution can be loaded.
        # Leave the objective-value check below to determine success.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    # Integral capacities give an integral maximum flow for this network.
    return {"objective": obj_val, "status": "optimal"}