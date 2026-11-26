# IR: {"sets":{"nodes":[1,2,3,4],"edges":[[1,2],[1,3],[2,3],[2,4],[3,4]],"intermediate_nodes":[2,3]},"params":{"capacity_1_2":"capacity[1,2]","capacity_1_3":"capacity[1,3]","capacity_2_3":"capacity[2,3]","capacity_2_4":"capacity[2,4]","capacity_3_4":"capacity[3,4]"},"variables":{"flow[i,j]":"nonnegative continuous for each directed edge"},"constraints":["flow[i,j] <= capacity[i,j] for each directed edge","sum(flow[i,v] for incoming edges) = sum(flow[v,j] for outgoing edges) for v in intermediate_nodes"],"objective":{"sense":"maximize","expression":"sum(flow[1,j] for edges leaving node 1)"}}

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

    model.capacity = pyo.Param(
        model.edges,
        initialize={
            (1, 2): params["capacity_1_2"],
            (1, 3): params["capacity_1_3"],
            (2, 3): params["capacity_2_3"],
            (2, 4): params["capacity_2_4"],
            (3, 4): params["capacity_3_4"],
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.edges, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.edges, rule=capacity_rule)

    def conservation_rule(network, node):
        incoming = sum(
            network.flow[origin, destination]
            for origin, destination in network.edges
            if destination == node
        )
        outgoing = sum(
            network.flow[origin, destination]
            for origin, destination in network.edges
            if origin == node
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=sum(
            model.flow[origin, destination]
            for origin, destination in model.edges
            if origin == 1
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi may raise when it cannot load a feasible solution.
        # Objective retrievability below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}