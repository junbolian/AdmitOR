# IR: {"sets":{"farms":[0,1,2,3,4,5,6],"substations":[0,1,2,3,4],"lines":[[0,1],[0,2],[1,0],[1,3],[2,2],[2,3],[3,1],[3,2],[3,3],[3,4],[4,0],[4,1],[5,3]]},"params":{},"variables":{"assigned[i,j]":"binary for (i,j) in lines"},"constraints":["For each farm i: sum(assigned[i,j] for feasible outgoing lines) <= 1.","For each substation j: sum(assigned[i,j] for feasible incoming lines) <= 1.","Assignments exist exclusively on lines."],"objective":"Maximize sum(assigned[i,j] for (i,j) in lines)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the maximum-cardinality matching problem; no parameters are required."""
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

    model.assigned = pyo.Var(model.lines, domain=pyo.Binary)

    def farm_limit_rule(grid, farm):
        # inequality() also represents the empty sum for farm 6 correctly.
        return pyo.inequality(
            None,
            pyo.quicksum(
                grid.assigned[origin, destination]
                for origin, destination in grid.lines
                if origin == farm
            ),
            1,
        )

    def substation_limit_rule(grid, substation):
        return pyo.inequality(
            None,
            pyo.quicksum(
                grid.assigned[origin, destination]
                for origin, destination in grid.lines
                if destination == substation
            ),
            1,
        )

    model.farm_limits = pyo.Constraint(model.farms, rule=farm_limit_rule)
    model.substation_limits = pyo.Constraint(
        model.substations, rule=substation_limit_rule
    )

    model.total_matches = pyo.Objective(
        expr=pyo.quicksum(
            model.assigned[origin, destination]
            for origin, destination in model.lines
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_matches))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}