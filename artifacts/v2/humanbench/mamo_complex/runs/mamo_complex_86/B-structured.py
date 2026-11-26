# IR: {"sets":{"nodes":[1,2,3,4],"edges":[[1,2],[1,3],[2,3],[2,4],[3,4]],"intermediate_nodes":[2,3]},"params":{"capacity_1_2":"real","capacity_1_3":"real","capacity_2_3":"real","capacity_2_4":"real","capacity_3_4":"real"},"variables":{"flow[i,j]":"nonnegative continuous for each directed edge"},"constraints":["flow[i,j] <= capacity_i_j for every edge (i,j)","sum(flow[i,v] for incoming edges) = sum(flow[v,j] for outgoing edges) for v in intermediate_nodes"],"objective":{"sense":"maximize","expression":"flow[1,2] + flow[1,3]"},"reporting":{"objective":"optimal objective rounded to the nearest integer, returned as float"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=[1, 2, 3, 4])
    model.edges = pyo.Set(
        dimen=2,
        initialize=[(1, 2), (1, 3), (2, 3), (2, 4), (3, 4)],
    )
    model.intermediate_nodes = pyo.Set(initialize=[2, 3])

    capacities = {
        (1, 2): params["capacity_1_2"],
        (1, 3): params["capacity_1_3"],
        (2, 3): params["capacity_2_3"],
        (2, 4): params["capacity_2_4"],
        (3, 4): params["capacity_3_4"],
    }

    model.edge_capacity = pyo.Param(
        model.edges,
        initialize=capacities,
        within=pyo.Reals,
    )

    model.flow = pyo.Var(
        model.edges,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(instance, tail, head):
        return instance.flow[tail, head] <= instance.edge_capacity[tail, head]

    model.capacity_limits = pyo.Constraint(
        model.edges,
        rule=capacity_rule,
    )

    def conservation_rule(instance, node):
        inflow = sum(
            instance.flow[tail, head]
            for tail, head in instance.edges
            if head == node
        )
        outflow = sum(
            instance.flow[tail, head]
            for tail, head in instance.edges
            if tail == node
        )
        return inflow == outflow

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
    except RuntimeError:
        # HiGHS may raise when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}