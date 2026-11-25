# IR: {"sets":{"N":"0..9","K":"0..1","A":[[0,1],[1,0],[0,4],[4,0],[1,2],[2,1],[1,3],[3,1],[1,5],[5,1],[1,6],[6,1],[2,3],[3,2],[3,4],[4,3],[4,5],[5,4],[5,6],[6,5],[5,9],[9,5],[6,7],[7,6],[7,8],[8,7],[7,9],[9,7],[8,9],[9,8]]},"params":{"arc_capacity":"params['arc_capacity'], indexed in A order; nonnegative","arc_cost":"params['arc_cost'], indexed in A order; retained as metadata","node_x":"params['node_x'], indexed by N; coordinate metadata","node_y":"params['node_y'], indexed by N; coordinate metadata","demand":"params['demand'], indexed by K; nonnegative","source":[1,7],"destination":[4,9]},"variables":{"flow[k,i,j]":"continuous nonnegative for k in K, (i,j) in A","max_utilization":"continuous in [0,1]"},"constraints":["For each k,n: sum outgoing flow[k,n,j] - sum incoming flow[k,i,n] = demand[k] if n=source[k], -demand[k] if n=destination[k], else 0.","For each (i,j): sum_k flow[k,i,j] <= arc_capacity[i,j].","For each (i,j): sum_k flow[k,i,j] <= max_utilization * arc_capacity[i,j]."],"objective":"Minimize max_utilization; arc costs and coordinates do not affect the objective."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1), (1, 0),
        (0, 4), (4, 0),
        (1, 2), (2, 1),
        (1, 3), (3, 1),
        (1, 5), (5, 1),
        (1, 6), (6, 1),
        (2, 3), (3, 2),
        (3, 4), (4, 3),
        (4, 5), (5, 4),
        (5, 6), (6, 5),
        (5, 9), (9, 5),
        (6, 7), (7, 6),
        (7, 8), (8, 7),
        (7, 9), (9, 7),
        (8, 9), (9, 8),
    )
    sources = (1, 7)
    destinations = (4, 9)

    capacities = params["arc_capacity"]
    costs = params["arc_cost"]
    x_coordinates = params["node_x"]
    y_coordinates = params["node_y"]
    demands = params["demand"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(10), ordered=True)
    model.requests = pyo.Set(initialize=range(2), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.arc_capacity = pyo.Param(
        model.arcs,
        initialize={
            arc: capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.arc_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: costs[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.node_x = pyo.Param(
        model.nodes,
        initialize={node: x_coordinates[node] for node in range(10)},
        within=pyo.Reals,
    )
    model.node_y = pyo.Param(
        model.nodes,
        initialize={node: y_coordinates[node] for node in range(10)},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.requests,
        initialize={request: demands[request] for request in range(2)},
        within=pyo.NonNegativeReals,
    )
    model.source_node = pyo.Param(
        model.requests,
        initialize={request: sources[request] for request in range(2)},
        within=model.nodes,
    )
    model.destination_node = pyo.Param(
        model.requests,
        initialize={
            request: destinations[request] for request in range(2)
        },
        within=model.nodes,
    )

    outgoing = {
        node: tuple(end for start, end in arcs if start == node)
        for node in range(10)
    }
    incoming = {
        node: tuple(start for start, end in arcs if end == node)
        for node in range(10)
    }

    model.flow = pyo.Var(
        model.requests, model.arcs, domain=pyo.NonNegativeReals
    )
    model.max_utilization = pyo.Var(
        domain=pyo.NonNegativeReals, bounds=(0, 1)
    )

    def flow_balance_rule(instance, request, node):
        if node == pyo.value(instance.source_node[request]):
            net_supply = instance.demand[request]
        elif node == pyo.value(instance.destination_node[request]):
            net_supply = -instance.demand[request]
        else:
            net_supply = 0

        return (
            sum(instance.flow[request, node, end] for end in outgoing[node])
            - sum(
                instance.flow[request, start, node]
                for start in incoming[node]
            )
            == net_supply
        )

    model.flow_balance = pyo.Constraint(
        model.requests, model.nodes, rule=flow_balance_rule
    )

    def capacity_rule(instance, start, end):
        return (
            sum(
                instance.flow[request, start, end]
                for request in instance.requests
            )
            <= instance.arc_capacity[start, end]
        )

    model.capacity_limit = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def utilization_rule(instance, start, end):
        return (
            sum(
                instance.flow[request, start, end]
                for request in instance.requests
            )
            <= instance.max_utilization * instance.arc_capacity[start, end]
        )

    model.utilization_limit = pyo.Constraint(
        model.arcs, rule=utilization_rule
    )

    model.objective = pyo.Objective(
        expr=model.max_utilization, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}