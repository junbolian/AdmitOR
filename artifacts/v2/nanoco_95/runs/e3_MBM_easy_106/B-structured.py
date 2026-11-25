# IR: {"sets":{"farms":[0,1,2,3,4,5,6],"substations":[0,1,2,3,4],"lines":[[0,1],[0,2],[1,0],[1,3],[2,2],[2,3],[3,1],[3,2],[3,3],[3,4],[4,0],[4,1],[5,3]]},"params":{},"variables":{"assignment[i,j]":{"type":"binary","indices":"lines"}},"constraints":["For each farm i: sum(assignment[i,j] for feasible outgoing lines) <= 1.","For each substation j: sum(assignment[i,j] for feasible incoming lines) <= 1.","Assignments exist only on lines."],"objective":{"sense":"maximize","expression":"sum(assignment[i,j] for (i,j) in lines)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Return the maximum matching objective; this problem has no numeric parameters."""
    model = pyo.ConcreteModel()

    model.farms = pyo.Set(initialize=range(7), ordered=True)
    model.substations = pyo.Set(initialize=range(5), ordered=True)
    model.lines = pyo.Set(
        dimen=2,
        initialize=[
            (0, 1), (0, 2),
            (1, 0), (1, 3),
            (2, 2), (2, 3),
            (3, 1), (3, 2), (3, 3), (3, 4),
            (4, 0), (4, 1),
            (5, 3),
        ],
        ordered=True,
    )

    model.assignment = pyo.Var(model.lines, domain=pyo.Binary)

    def farm_capacity_rule(grid, farm):
        outgoing = [
            grid.assignment[source, destination]
            for source, destination in grid.lines
            if source == farm
        ]
        if not outgoing:
            return pyo.Constraint.Feasible
        return pyo.quicksum(outgoing) <= 1

    def substation_capacity_rule(grid, substation):
        return pyo.quicksum(
            grid.assignment[source, destination]
            for source, destination in grid.lines
            if destination == substation
        ) <= 1

    model.farm_capacity = pyo.Constraint(
        model.farms, rule=farm_capacity_rule
    )
    model.substation_capacity = pyo.Constraint(
        model.substations, rule=substation_capacity_rule
    )

    model.total_matches = pyo.Objective(
        expr=pyo.quicksum(
            model.assignment[source, destination]
            for source, destination in model.lines
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise when it cannot load a feasible solution.
        # Success is determined solely by objective retrievability below.
        pass

    try:
        obj_val = float(pyo.value(model.total_matches))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}