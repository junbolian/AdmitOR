# IR: {"sets":{"N":"0..8","E":[[0,1],[0,3],[0,5],[1,2],[1,7],[2,3],[2,6],[2,7],[3,4],[4,5],[4,6],[5,6],[6,7],[7,8]],"A":"each edge in E followed immediately by its reverse","K":[1,2]},"params":{"arc_capacity":"params['arc_capacity']: directed-arc tuple-keyed mapping, 9x9 matrix, 28-entry arc-order sequence, or 14-entry edge-order sequence shared by both directions; nonnegative","arc_cost":"params['arc_cost']: same supported layouts as arc_capacity; real","demand_commodity1":"params['demand_commodity1']; nonnegative","demand_commodity2":"params['demand_commodity2']; nonnegative","source":{"1":3,"2":6},"sink":{"1":2,"2":1}},"variables":{"flow[k,i,j]":"nonnegative real for k in K and (i,j) in A"},"constraints":["For each k,v: sum_j flow[k,v,j] - sum_i flow[k,i,v] = demand[k]*(1[v=source[k]]-1[v=sink[k]])","For each (i,j) in A: sum_k flow[k,i,j] <= arc_capacity[i,j]"],"objective":"minimize sum_(i,j) in A sum_k in K arc_cost[i,j]*flow[k,i,j]"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _arc_values(data, edges, arcs, parameter_name):
    """Normalize tuple-keyed mappings, matrices, and ordered sequences."""
    if isinstance(data, Mapping):
        return {arc: data[arc] for arc in arcs}

    if len(data) == 9:
        return {
            (origin, destination): data[origin][destination]
            for origin, destination in arcs
        }

    if len(data) == len(arcs):
        return {
            arc: data[position]
            for position, arc in enumerate(arcs)
        }

    if len(data) == len(edges):
        return {
            directed_arc: data[position]
            for position, (origin, destination) in enumerate(edges)
            for directed_arc in (
                (origin, destination),
                (destination, origin),
            )
        }

    raise ValueError(
        f"{parameter_name} must be a directed-arc tuple-keyed mapping, "
        "a 9x9 matrix, a 28-entry directed-arc sequence, "
        "or a 14-entry undirected-edge sequence."
    )


def solve(params):
    edges = (
        (0, 1), (0, 3), (0, 5), (1, 2), (1, 7),
        (2, 3), (2, 6), (2, 7), (3, 4), (4, 5),
        (4, 6), (5, 6), (6, 7), (7, 8),
    )
    arcs = tuple(
        directed_arc
        for origin, destination in edges
        for directed_arc in (
            (origin, destination),
            (destination, origin),
        )
    )

    capacities = _arc_values(
        params["arc_capacity"], edges, arcs, "arc_capacity"
    )
    costs = _arc_values(
        params["arc_cost"], edges, arcs, "arc_cost"
    )
    demands = {
        1: params["demand_commodity1"],
        2: params["demand_commodity2"],
    }
    sources = {1: 3, 2: 6}
    sinks = {1: 2, 2: 1}

    outgoing = {
        node: tuple(
            destination
            for origin, destination in arcs
            if origin == node
        )
        for node in range(9)
    }
    incoming = {
        node: tuple(
            origin
            for origin, destination in arcs
            if destination == node
        )
        for node in range(9)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(9), ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.commodities = pyo.Set(initialize=(1, 2), ordered=True)

    model.lane_capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize=costs,
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.commodities,
        initialize=demands,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(
        model.commodities,
        model.arcs,
        domain=pyo.NonNegativeReals,
    )

    def balance_rule(problem, commodity, node):
        net_outflow = sum(
            problem.flow[commodity, node, destination]
            for destination in outgoing[node]
        ) - sum(
            problem.flow[commodity, origin, node]
            for origin in incoming[node]
        )
        balance_sign = (
            int(node == sources[commodity])
            - int(node == sinks[commodity])
        )
        return net_outflow == balance_sign * problem.demand[commodity]

    model.flow_balance = pyo.Constraint(
        model.commodities,
        model.nodes,
        rule=balance_rule,
    )

    def capacity_rule(problem, origin, destination):
        return sum(
            problem.flow[commodity, origin, destination]
            for commodity in problem.commodities
        ) <= problem.lane_capacity[origin, destination]

    model.shared_capacity = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination]
            * model.flow[commodity, origin, destination]
            for origin, destination in model.arcs
            for commodity in model.commodities
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected runtime errors must still propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}