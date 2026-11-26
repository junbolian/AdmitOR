# IR: {"sets":{"N":"range(num_cities)","A":"{(i,j) in N x N: i != j}"},"params":{"capacity":"nonnegative directed capacity matrix; diagonal ignored","num_cities":"params['num_cities'], frozen","source":"params['source'], frozen","destination":"params['destination'], frozen"},"variables":{"flow[i,j]":"continuous nonnegative, (i,j) in A","total_flow":"continuous nonnegative"},"constraints":["flow[i,j] <= capacity[i][j] for (i,j) in A","sum_j flow[i,j] - sum_j flow[j,i] = total_flow if i=source, -total_flow if i=destination, 0 otherwise, for i in N"],"objective":"maximize total_flow"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    num_cities = params["num_cities"]
    source = params["source"]
    destination = params["destination"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(
        initialize=range(num_cities),
        ordered=True,
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(num_cities)
            for j in range(num_cities)
            if i != j
        ],
    )

    model.road_capacity = pyo.Param(
        model.arcs,
        initialize=lambda _, i, j: capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.total_flow = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.road_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def balance_rule(network, i):
        outgoing = sum(
            network.flow[i, j] for j in network.nodes if j != i
        )
        incoming = sum(
            network.flow[j, i] for j in network.nodes if j != i
        )
        if i == source:
            return outgoing - incoming == network.total_flow
        if i == destination:
            return outgoing - incoming == -network.total_flow
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(
        model.nodes,
        rule=balance_rule,
    )
    model.max_flow_objective = pyo.Objective(
        expr=model.total_flow,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}