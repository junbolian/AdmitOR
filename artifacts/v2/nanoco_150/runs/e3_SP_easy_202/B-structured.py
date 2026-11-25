# IR: {"sets":{"N":"0..9","D":"0..1","A":[[0,1],[0,2],[0,6],[0,8],[1,2],[2,3],[2,7],[3,4],[4,5],[4,7],[4,8],[5,6],[5,9],[6,7],[6,8],[7,8],[8,9]]},"params":{"capacities":"Nonnegative real per arc, supplied in A order","costs":"Real per arc, supplied in A order","supplies":"Real net supply per node","coordinates":"Real geographical coordinate per (node,dimension); metadata only"},"variables":{"flow[A]":"Nonnegative continuous real"},"constraints":{"capacity":"flow[i,j] <= capacities[i,j] for every (i,j) in A","balance":"sum(flow[i,j] for outgoing arcs) - sum(flow[j,i] for incoming arcs) = supplies[i] for every i in N"},"objective":"Minimize sum(costs[i,j] * flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_order = (
        (0, 1),
        (0, 2),
        (0, 6),
        (0, 8),
        (1, 2),
        (2, 3),
        (2, 7),
        (3, 4),
        (4, 5),
        (4, 7),
        (4, 8),
        (5, 6),
        (5, 9),
        (6, 7),
        (6, 8),
        (7, 8),
        (8, 9),
    )

    capacities = params["capacities"]
    costs = params["costs"]
    supplies = params["supplies"]
    coordinates = params["coordinates"]

    if len(capacities) != len(arc_order):
        raise ValueError("capacities must contain exactly 17 entries.")
    if len(costs) != len(arc_order):
        raise ValueError("costs must contain exactly 17 entries.")
    if len(supplies) != 10:
        raise ValueError("supplies must contain exactly 10 entries.")
    if len(coordinates) != 10 or any(
        len(point) != 2 for point in coordinates
    ):
        raise ValueError("coordinates must contain exactly 10 coordinate pairs.")

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 9)
    model.dimensions = pyo.RangeSet(0, 1)
    model.arcs = pyo.Set(dimen=2, initialize=arc_order, ordered=True)

    model.arc_capacity = pyo.Param(
        model.arcs,
        initialize={
            arc: capacities[position]
            for position, arc in enumerate(arc_order)
        },
        within=pyo.NonNegativeReals,
    )
    model.arc_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: costs[position]
            for position, arc in enumerate(arc_order)
        },
        within=pyo.Reals,
    )
    model.net_supply = pyo.Param(
        model.nodes,
        initialize={node: supplies[node] for node in range(10)},
        within=pyo.Reals,
    )
    model.node_coordinates = pyo.Param(
        model.nodes,
        model.dimensions,
        initialize={
            (node, dimension): coordinates[node][dimension]
            for node in range(10)
            for dimension in range(2)
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(instance, origin, destination):
        return (
            instance.flow[origin, destination]
            <= instance.arc_capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(instance, node):
        outgoing = sum(
            instance.flow[origin, destination]
            for origin, destination in instance.arcs
            if origin == node
        )
        incoming = sum(
            instance.flow[origin, destination]
            for origin, destination in instance.arcs
            if destination == node
        )
        return outgoing - incoming == instance.net_supply[node]

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}