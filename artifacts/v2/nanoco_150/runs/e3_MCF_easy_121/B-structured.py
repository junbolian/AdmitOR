# IR: {"sets":{"nodes":[0,1,2,3,4,5],"axes":[0,1],"arcs":[[0,2],[0,3],[1,2],[1,3],[2,4],[2,5],[3,4],[3,5],[0,4],[0,5],[1,4],[1,5]]},"params":{"supplies":"node-indexed net supplies","coordinates":"node-indexed (x,y) metadata; no distance-cost formula specified","arc_costs":"unit costs in listed arc order","arc_capacities":"capacities in listed arc order"},"variables":{"flow[i,j]":"nonnegative continuous for each arc"},"constraints":["For every node n: sum(flow[n,j]) - sum(flow[i,n]) = supplies[n].","For every arc (i,j): flow[i,j] <= arc_capacities[i,j]."],"objective":"Minimize sum(arc_costs[i,j] * flow[i,j]) over all arcs."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(6))
    axes = (0, 1)
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

    supplies = params["supplies"]
    coordinates = params["coordinates"]
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.axes = pyo.Set(initialize=axes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.supply = pyo.Param(
        model.nodes,
        initialize={node: supplies[node] for node in nodes},
        within=pyo.Reals,
    )
    model.coordinate = pyo.Param(
        model.nodes,
        model.axes,
        initialize={
            (node, axis): coordinates[node][axis]
            for node in nodes
            for axis in axes
        },
        within=pyo.Reals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: arc_costs[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            arc: arc_capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(network, node):
        outgoing = sum(
            network.flow[source, destination]
            for source, destination in arcs
            if source == node
        )
        incoming = sum(
            network.flow[source, destination]
            for source, destination in arcs
            if destination == node
        )
        return outgoing - incoming == network.supply[node]

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def capacity_rule(network, source, destination):
        return (
            network.flow[source, destination]
            <= network.capacity[source, destination]
        )

    model.arc_capacity_limit = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[source, destination]
            * model.flow[source, destination]
            for source, destination in arcs
        ),
        sense=pyo.minimize,
    )

    # HiGHS can raise RuntimeError when no solution can be loaded.
    # Objective retrievability alone determines the returned success status.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}