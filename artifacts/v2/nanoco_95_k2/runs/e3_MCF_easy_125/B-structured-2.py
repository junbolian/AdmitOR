# IR: {"sets":{"N":[0,1,2,3,4,5],"A":[[0,2],[0,3],[1,2],[1,3],[2,4],[2,5],[3,4],[3,5],[0,4],[0,5],[1,4],[1,5]]},"params":{"supply[n]":"params['supply_node{n}'] for n in N","coord_x[n]":"params['coord_x'][n] for n in N; informational only","coord_y[n]":"params['coord_y'][n] for n in N; informational only","capacity[i,j]":"params['capacity_{i}_{j}'] for (i,j) in A","cost[i,j]":"params['cost_{i}_{j}'] for (i,j) in A"},"variables":{"flow[i,j]":{"type":"continuous","lower_bound":0,"index":"A"}},"constraints":["balance[n]: sum(flow[n,j] for outgoing arcs) - sum(flow[i,n] for incoming arcs) == supply[n], for n in N","arc_limit[i,j]: flow[i,j] <= capacity[i,j], for (i,j) in A"],"objective":{"sense":"minimize","expression":"sum(cost[i,j] * flow[i,j] for (i,j) in A)"}}

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

    supplies = {
        0: params["supply_node0"],
        1: params["supply_node1"],
        2: params["supply_node2"],
        3: params["supply_node3"],
        4: params["supply_node4"],
        5: params["supply_node5"],
    }
    capacities = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }
    costs = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin, destination in arcs
    }
    x_coordinates = {node: params["coord_x"][node] for node in nodes}
    y_coordinates = {node: params["coord_y"][node] for node in nodes}

    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.supply = pyo.Param(
        model.nodes, initialize=supplies, within=pyo.Reals
    )
    model.coord_x = pyo.Param(
        model.nodes, initialize=x_coordinates, within=pyo.Reals
    )
    model.coord_y = pyo.Param(
        model.nodes, initialize=y_coordinates, within=pyo.Reals
    )
    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.NonNegativeReals
    )
    model.unit_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(network, node):
        return (
            sum(network.flow[arc] for arc in outgoing[node])
            - sum(network.flow[arc] for arc in incoming[node])
            == network.supply[node]
        )

    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def arc_limit_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.arc_limit = pyo.Constraint(model.arcs, rule=arc_limit_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}