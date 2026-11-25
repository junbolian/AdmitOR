# IR: {"sets":{"N":[0,1,2,3,4,5],"A":[[0,2],[0,3],[1,2],[1,3],[2,4],[2,5],[3,4],[3,5],[0,4],[0,5],[1,4],[1,5]]},"params":{"supply[i]":"params['supply_node{i}'], i in N","coord_x[i]":"params['coord_x'][i], i in N; geographic metadata","coord_y[i]":"params['coord_y'][i], i in N; geographic metadata","capacity[i,j]":"params['capacity_{i}_{j}'], (i,j) in A","cost[i,j]":"params['cost_{i}_{j}'], (i,j) in A"},"variables":{"flow[i,j]":"nonnegative continuous, (i,j) in A"},"constraints":["For each i in N: sum(flow[i,j] for outgoing arcs) - sum(flow[j,i] for incoming arcs) = supply[i].","For each (i,j) in A: flow[i,j] <= capacity[i,j]."],"objective":"Minimize sum(cost[i,j] * flow[i,j] for (i,j) in A)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(6))
    arcs = (
        (0, 2), (0, 3), (1, 2), (1, 3),
        (2, 4), (2, 5), (3, 4), (3, 5),
        (0, 4), (0, 5), (1, 4), (1, 5),
    )

    supply = {
        0: params["supply_node0"],
        1: params["supply_node1"],
        2: params["supply_node2"],
        3: params["supply_node3"],
        4: params["supply_node4"],
        5: params["supply_node5"],
    }

    coord_x = params["coord_x"]
    coord_y = params["coord_y"]

    capacities = {
        (0, 2): params["capacity_0_2"],
        (0, 3): params["capacity_0_3"],
        (1, 2): params["capacity_1_2"],
        (1, 3): params["capacity_1_3"],
        (2, 4): params["capacity_2_4"],
        (2, 5): params["capacity_2_5"],
        (3, 4): params["capacity_3_4"],
        (3, 5): params["capacity_3_5"],
        (0, 4): params["capacity_0_4"],
        (0, 5): params["capacity_0_5"],
        (1, 4): params["capacity_1_4"],
        (1, 5): params["capacity_1_5"],
    }

    costs = {
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (0, 4): params["cost_0_4"],
        (0, 5): params["cost_0_5"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.supply = pyo.Param(
        model.nodes, initialize=supply, within=pyo.Reals
    )
    model.coord_x = pyo.Param(
        model.nodes,
        initialize={node: coord_x[node] for node in nodes},
        within=pyo.Reals,
    )
    model.coord_y = pyo.Param(
        model.nodes,
        initialize={node: coord_y[node] for node in nodes},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.Reals
    )
    model.cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }

    def balance_rule(network, node):
        return (
            sum(network.flow[arc] for arc in outgoing[node])
            - sum(network.flow[arc] for arc in incoming[node])
            == network.supply[node]
        )

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)
    model.arc_capacity = pyo.Constraint(model.arcs, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}