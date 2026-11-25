# IR: {"sets":{"N":"range(num_nodes)","K":"range(num_arcs)","D":[0,1],"arcs":[[0,1],[1,2],[1,7],[2,3],[2,6],[3,4],[3,8],[3,9],[4,5],[4,8],[5,6],[6,7],[7,8],[7,9],[8,9]]},"params":{"capacities":"nonnegative vector indexed by K","costs":"real vector indexed by K","node_coordinates":"real matrix indexed by N,D; descriptive only","source_node":"member of N","sink_node":"distinct member of N","num_nodes":"number of nodes","num_arcs":"number of arcs"},"variables":{"flow[k]":"continuous nonnegative","delivered":"continuous nonnegative"},"constraints":["flow[k] <= capacities[k] for every k","outflow[i] - inflow[i] = delivered if i=source_node, -delivered if i=sink_node, otherwise 0","stage 2 only: delivered = stage 1 maximum"},"objective":{"priority_1":"maximize delivered","priority_2":"minimize sum(costs[k]*flow[k]) with delivered fixed at its maximum","returned_objective":"maximum delivered volume after both stages succeed"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _solve_stage(model, objective):
    """Solve one stage; determine success only by objective retrieval."""
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}


def solve(params):
    capacities = params["capacities"]
    costs = params["costs"]
    node_coordinates = params["node_coordinates"]
    source_node = params["source_node"]
    sink_node = params["sink_node"]
    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]

    arcs = (
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

    if num_nodes != 10 or num_arcs != len(arcs):
        return {"objective": None, "status": "invalid_network_size"}
    if source_node not in range(num_nodes):
        return {"objective": None, "status": "invalid_source"}
    if sink_node not in range(num_nodes) or source_node == sink_node:
        return {"objective": None, "status": "invalid_sink"}

    outgoing = {
        node: tuple(k for k, (tail, head) in enumerate(arcs) if tail == node)
        for node in range(num_nodes)
    }
    incoming = {
        node: tuple(k for k, (tail, head) in enumerate(arcs) if head == node)
        for node in range(num_nodes)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.arc_ids = pyo.Set(initialize=range(num_arcs), ordered=True)
    model.dimensions = pyo.Set(initialize=(0, 1), ordered=True)

    model.route_capacity = pyo.Param(
        model.arc_ids,
        initialize={k: capacities[k] for k in range(num_arcs)},
        within=pyo.NonNegativeReals,
    )
    model.route_cost = pyo.Param(
        model.arc_ids,
        initialize={k: costs[k] for k in range(num_arcs)},
        within=pyo.Reals,
    )
    model.coordinates = pyo.Param(
        model.nodes,
        model.dimensions,
        initialize={
            (node, dimension): node_coordinates[node][dimension]
            for node in range(num_nodes)
            for dimension in (0, 1)
        },
        within=pyo.Reals,
    )
    model.supply_origin = pyo.Param(
        initialize=source_node, within=model.nodes
    )
    model.disaster_destination = pyo.Param(
        initialize=sink_node, within=model.nodes
    )

    model.flow = pyo.Var(model.arc_ids, domain=pyo.NonNegativeReals)
    model.delivered = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, k):
        return network.flow[k] <= network.route_capacity[k]

    model.capacity_limits = pyo.Constraint(
        model.arc_ids, rule=capacity_rule
    )

    def balance_rule(network, node):
        net_outflow = (
            pyo.quicksum(network.flow[k] for k in outgoing[node])
            - pyo.quicksum(network.flow[k] for k in incoming[node])
        )
        if node == source_node:
            return net_outflow == network.delivered
        if node == sink_node:
            return net_outflow == -network.delivered
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    model.maximum_flow = pyo.Objective(
        expr=model.delivered,
        sense=pyo.maximize,
    )
    model.minimum_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.route_cost[k] * model.flow[k] for k in model.arc_ids
        ),
        sense=pyo.minimize,
    )
    model.minimum_cost.deactivate()

    first_stage = _solve_stage(model, model.maximum_flow)
    if first_stage["objective"] is None:
        return first_stage

    model.required_delivery = pyo.Param(
        initialize=first_stage["objective"],
        within=pyo.NonNegativeReals,
    )
    model.preserve_maximum_flow = pyo.Constraint(
        expr=model.delivered == model.required_delivery
    )
    model.maximum_flow.deactivate()
    model.minimum_cost.activate()

    # Clear previous primal values so objective retrieval cannot use stale data.
    for k in model.arc_ids:
        model.flow[k].set_value(None)
    model.delivered.set_value(None)

    second_stage = _solve_stage(model, model.minimum_cost)
    if second_stage["objective"] is None:
        return second_stage

    # The loaded flows now minimize cost among all maximum-flow solutions.
    # Report the primary objective: maximum delivered supply volume.
    try:
        obj_val = float(pyo.value(model.maximum_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}