# IR: {"sets":{"N":"0..params['num_nodes']-1","A":"[(0,1),(1,2),(1,7),(2,3),(2,6),(3,4),(3,8),(3,9),(4,5),(4,8),(5,6),(6,7),(7,8),(7,9),(8,9)]","D":[0,1]},"params":{"capacity[a]":"params['capacities'][a]","cost[a]":"params['costs'][a]","coordinate[v,d]":"params['node_coordinates'][v][d], descriptive only","s":"params['source_node']","t":"params['sink_node']","n":"params['num_nodes']","k":"params['num_arcs']"},"variables":{"flow[a]":"nonnegative continuous","delivered":"nonnegative continuous"},"constraints":["flow[a] <= capacity[a] for every arc a","sum(outgoing flow[v])-sum(incoming flow[v]) = delivered if v=s, -delivered if v=t, and 0 otherwise","stage 2 only: delivered = stage 1 optimal delivered"},"objective":{"stage_1":"maximize delivered","stage_2":"minimize sum(cost[a]*flow[a]) with delivered fixed at its stage 1 optimum","returned_objective":"maximum delivered volume; final model solution also minimizes cost at that volume"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    costs = params["costs"]
    node_coordinates = params["node_coordinates"]
    source_node = params["source_node"]
    sink_node = params["sink_node"]
    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]

    arc_endpoints = (
        (0, 1),
        (1, 2),
        (1, 7),
        (2, 3),
        (2, 6),
        (3, 4),
        (3, 8),
        (3, 9),
        (4, 5),
        (4, 8),
        (5, 6),
        (6, 7),
        (7, 8),
        (7, 9),
        (8, 9),
    )

    if num_nodes != 10 or num_arcs != len(arc_endpoints):
        return {"objective": None, "status": "invalid_network_size"}
    if len(capacities) != num_arcs or len(costs) != num_arcs:
        return {"objective": None, "status": "invalid_arc_data"}
    if len(node_coordinates) != num_nodes:
        return {"objective": None, "status": "invalid_coordinates"}
    if any(len(node_coordinates[node]) != 2 for node in range(num_nodes)):
        return {"objective": None, "status": "invalid_coordinates"}
    if (
        source_node not in range(num_nodes)
        or sink_node not in range(num_nodes)
        or source_node == sink_node
    ):
        return {"objective": None, "status": "invalid_terminals"}
    if any(capacities[arc] < 0 for arc in range(num_arcs)):
        return {"objective": None, "status": "negative_capacity"}

    outgoing = {
        node: tuple(
            arc
            for arc, (tail, head) in enumerate(arc_endpoints)
            if tail == node
        )
        for node in range(num_nodes)
    }
    incoming = {
        node: tuple(
            arc
            for arc, (tail, head) in enumerate(arc_endpoints)
            if head == node
        )
        for node in range(num_nodes)
    }

    model = pyo.ConcreteModel()
    model.node_ids = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.arc_ids = pyo.Set(initialize=range(num_arcs), ordered=True)
    model.coordinate_axes = pyo.Set(initialize=(0, 1), ordered=True)

    model.route_capacity = pyo.Param(
        model.arc_ids,
        initialize={arc: capacities[arc] for arc in range(num_arcs)},
        within=pyo.NonNegativeReals,
    )
    model.route_cost = pyo.Param(
        model.arc_ids,
        initialize={arc: costs[arc] for arc in range(num_arcs)},
        within=pyo.Reals,
    )
    model.location_coordinate = pyo.Param(
        model.node_ids,
        model.coordinate_axes,
        initialize={
            (node, axis): node_coordinates[node][axis]
            for node in range(num_nodes)
            for axis in (0, 1)
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arc_ids, domain=pyo.NonNegativeReals)
    model.delivered = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, arc):
        return network.flow[arc] <= network.route_capacity[arc]

    model.capacity_limits = pyo.Constraint(
        model.arc_ids, rule=capacity_rule
    )

    def balance_rule(network, node):
        net_outflow = (
            pyo.quicksum(network.flow[arc] for arc in outgoing[node])
            - pyo.quicksum(network.flow[arc] for arc in incoming[node])
        )
        if node == source_node:
            return net_outflow == network.delivered
        if node == sink_node:
            return net_outflow == -network.delivered
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.node_ids, rule=balance_rule
    )

    model.volume_objective = pyo.Objective(
        expr=model.delivered,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.volume_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    maximum_volume = obj_val
    model.volume_objective.deactivate()
    model.maximum_volume_requirement = pyo.Constraint(
        expr=model.delivered == maximum_volume
    )
    model.cost_objective = pyo.Objective(
        expr=pyo.quicksum(
            model.route_cost[arc] * model.flow[arc]
            for arc in model.arc_ids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.cost_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    # Report the primary objective after verifying the cost-minimizing solve.
    try:
        obj_val = float(pyo.value(model.volume_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}