# IR: {"sets":{"N":"0..9","I":"1..8","D":[0,1],"A":[[0,1],[1,2],[1,4],[1,5],[1,7],[2,3],[3,4],[4,5],[4,8],[4,9],[5,6],[5,7],[6,7],[7,8],[8,9]]},"params":{"capacities":"nonnegative real[A], read from params in arc order","unit_costs":"real[A], read from params in arc order; unused in objective","node_coordinates":"real[N,D], read from params; frozen geometry only"},"variables":{"flow":"nonnegative real[A]"},"constraints":["flow[i,j] <= capacities[i,j] for (i,j) in A","sum(flow[i,v] for (i,v) in A) == sum(flow[v,j] for (v,j) in A) for v in I"],"objective":"maximize sum(flow[i,9] for (i,9) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1),
        (1, 2),
        (1, 4),
        (1, 5),
        (1, 7),
        (2, 3),
        (3, 4),
        (4, 5),
        (4, 8),
        (4, 9),
        (5, 6),
        (5, 7),
        (6, 7),
        (7, 8),
        (8, 9),
    )

    capacities = params["capacities"]
    unit_costs = params["unit_costs"]
    node_coordinates = params["node_coordinates"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 9)
    model.intermediate_nodes = pyo.RangeSet(1, 8)
    model.dimensions = pyo.Set(initialize=(0, 1), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacities = pyo.Param(
        model.arcs,
        initialize={arc: capacities[idx] for idx, arc in enumerate(arcs)},
        within=pyo.NonNegativeReals,
        mutable=False,
    )
    model.unit_costs = pyo.Param(
        model.arcs,
        initialize={arc: unit_costs[idx] for idx, arc in enumerate(arcs)},
        within=pyo.Reals,
        mutable=False,
    )
    model.node_coordinates = pyo.Param(
        model.nodes,
        model.dimensions,
        initialize={
            (node, dimension): node_coordinates[node][dimension]
            for node in range(10)
            for dimension in range(2)
        },
        within=pyo.Reals,
        mutable=False,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(grid, origin, destination):
        return (
            grid.flow[origin, destination]
            <= grid.capacities[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(grid, node):
        inflow = sum(
            grid.flow[origin, destination]
            for origin, destination in arcs
            if destination == node
        )
        outflow = sum(
            grid.flow[origin, destination]
            for origin, destination in arcs
            if origin == node
        )
        return inflow == outflow

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes,
        rule=conservation_rule,
    )

    model.total_delivered = pyo.Objective(
        expr=sum(
            model.flow[origin, destination]
            for origin, destination in arcs
            if destination == 9
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_delivered))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}