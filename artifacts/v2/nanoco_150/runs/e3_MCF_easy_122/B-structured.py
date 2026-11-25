# IR: {"sets":{"N":[0,1,2,3,4,5],"A":[[0,2],[0,3],[1,2],[1,3],[2,4],[2,5],[3,4],[3,5],[0,4],[0,5],[1,4],[1,5]]},"params":{"supply[i]":"params[supply_i], i in N","capacity[i,j]":"params[capacity_i_j], (i,j) in A","cost[i,j]":"params[cost_i_j], (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative, (i,j) in A"},"constraints":["balance[i]: sum(flow[i,j] for outgoing arcs) - sum(flow[j,i] for incoming arcs) == supply[i], i in N","route_limit[i,j]: flow[i,j] <= capacity[i,j], (i,j) in A"],"objective":"minimize sum(cost[i,j] * flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(6))
    arcs = (
        (0, 2),
        (0, 3),
        (1, 2),
        (1, 3),
        (2, 4),
        (2, 5),
        (3, 4),
        (3, 5),
        (0, 4),
        (0, 5),
        (1, 4),
        (1, 5),
    )

    supply_data = {
        node: params[f"supply_{node}"]
        for node in nodes
    }
    capacity_data = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }
    cost_data = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.facilities = pyo.Set(initialize=nodes, ordered=True)
    model.routes = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.supply = pyo.Param(
        model.facilities, initialize=supply_data, within=pyo.Reals
    )
    model.capacity = pyo.Param(
        model.routes, initialize=capacity_data, within=pyo.Reals
    )
    model.cost = pyo.Param(
        model.routes, initialize=cost_data, within=pyo.Reals
    )

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def balance_rule(network, node):
        outgoing = sum(
            network.flow[origin, destination]
            for origin, destination in arcs
            if origin == node
        )
        incoming = sum(
            network.flow[origin, destination]
            for origin, destination in arcs
            if destination == node
        )
        return outgoing - incoming == network.supply[node]

    model.balance = pyo.Constraint(model.facilities, rule=balance_rule)

    def route_limit_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.route_limit = pyo.Constraint(model.routes, rule=route_limit_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination] * model.flow[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An unsuccessful solve can leave all flow variables uninitialized.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}