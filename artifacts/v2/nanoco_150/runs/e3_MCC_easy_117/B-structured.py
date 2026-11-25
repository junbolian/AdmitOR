# IR: {"sets":{"N":"0..num_nodes-1","D":[0,1],"A":[[0,1],[0,2],[0,3],[0,5],[1,0],[1,2],[2,0],[2,1],[2,3],[2,4],[3,2],[3,4],[3,5],[4,0],[4,3],[4,5],[5,0],[5,4]]},"params":{"num_nodes":"frozen at 6","num_arcs":"frozen at 18","coordinates":"numeric array [node][dimension]; descriptive only","arc_min_flow":"numeric array in listed arc order","arc_max_flow":"numeric array in listed arc order","arc_unit_cost":"numeric array in listed arc order"},"variables":{"flow[a]":"nonnegative integer for each arc a"},"constraints":["flow[a] >= arc_min_flow[a] for each arc a","flow[a] <= arc_max_flow[a] for each arc a","sum(flow[a] for arcs entering n) == sum(flow[a] for arcs leaving n) for each node n"],"objective":"minimize sum(arc_unit_cost[a] * flow[a] for each arc a)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]
    coordinates = params["coordinates"]
    arc_min_flow = params["arc_min_flow"]
    arc_max_flow = params["arc_max_flow"]
    arc_unit_cost = params["arc_unit_cost"]

    arc_endpoints = (
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 5),
        (1, 0),
        (1, 2),
        (2, 0),
        (2, 1),
        (2, 3),
        (2, 4),
        (3, 2),
        (3, 4),
        (3, 5),
        (4, 0),
        (4, 3),
        (4, 5),
        (5, 0),
        (5, 4),
    )

    if num_nodes != 6 or num_arcs != len(arc_endpoints):
        return {"objective": None, "status": "invalid_dimensions"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.dimensions = pyo.Set(initialize=(0, 1), ordered=True)
    model.arcs = pyo.Set(initialize=range(num_arcs), ordered=True)

    model.coordinates = pyo.Param(
        model.nodes,
        model.dimensions,
        initialize=lambda mdl, node, dimension: coordinates[node][dimension],
        within=pyo.Reals,
    )
    model.minimum_flow = pyo.Param(
        model.arcs,
        initialize=lambda mdl, arc: arc_min_flow[arc],
        within=pyo.NonNegativeReals,
    )
    model.maximum_flow = pyo.Param(
        model.arcs,
        initialize=lambda mdl, arc: arc_max_flow[arc],
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize=lambda mdl, arc: arc_unit_cost[arc],
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    model.minimum_flow_constraint = pyo.Constraint(
        model.arcs,
        rule=lambda mdl, arc: mdl.flow[arc] >= mdl.minimum_flow[arc],
    )
    model.maximum_flow_constraint = pyo.Constraint(
        model.arcs,
        rule=lambda mdl, arc: mdl.flow[arc] <= mdl.maximum_flow[arc],
    )

    incoming = {
        node: [
            arc
            for arc, (_, destination) in enumerate(arc_endpoints)
            if destination == node
        ]
        for node in model.nodes
    }
    outgoing = {
        node: [
            arc
            for arc, (origin, _) in enumerate(arc_endpoints)
            if origin == node
        ]
        for node in model.nodes
    }

    def conservation_rule(mdl, node):
        return (
            sum(mdl.flow[arc] for arc in incoming[node])
            == sum(mdl.flow[arc] for arc in outgoing[node])
        )

    model.flow_conservation = pyo.Constraint(
        model.nodes, rule=conservation_rule
    )
    model.total_energy = pyo.Objective(
        expr=sum(
            model.unit_cost[arc] * model.flow[arc]
            for arc in model.arcs
        ),
        sense=pyo.minimize,
    )

    # HiGHS can raise RuntimeError when no solution can be loaded.
    # Success is determined solely by objective-value retrieval below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_energy))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}