# IR: {"sets":{"F":[0,1,2,3,4,5,6],"S":[0,1,2,3,4],"E":[[0,1],[0,2],[1,0],[1,3],[2,2],[2,3],[3,1],[3,2],[3,3],[3,4],[4,0],[4,1],[5,3]]},"params":{},"variables":{"x[f,s]":{"type":"binary","index":"E"}},"constraints":["For each f in F: sum(x[f,s] for (f,s) in E) <= 1","For each s in S: sum(x[f,s] for (f,s) in E) <= 1","Variables exist exclusively on E"],"objective":{"sense":"maximize","expression":"sum(x[f,s] for (f,s) in E)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # PARAMS is empty; all supplied problem data describe fixed structure.
    feasible_lines = (
        (0, 1), (0, 2),
        (1, 0), (1, 3),
        (2, 2), (2, 3),
        (3, 1), (3, 2), (3, 3), (3, 4),
        (4, 0), (4, 1),
        (5, 3),
    )

    model = pyo.ConcreteModel()
    model.farms = pyo.RangeSet(0, 6)
    model.substations = pyo.RangeSet(0, 4)
    model.feasible_lines = pyo.Set(
        dimen=2,
        initialize=feasible_lines,
        within=model.farms * model.substations,
    )
    model.x = pyo.Var(model.feasible_lines, domain=pyo.Binary)

    def farm_limit_rule(grid, farm):
        destinations = [
            substation
            for source, substation in grid.feasible_lines
            if source == farm
        ]
        if not destinations:
            # Farm 6 has no incident lines, so its constraint is 0 <= 1.
            return pyo.Constraint.Feasible
        return sum(grid.x[farm, substation] for substation in destinations) <= 1

    def substation_limit_rule(grid, substation):
        return sum(
            grid.x[farm, destination]
            for farm, destination in grid.feasible_lines
            if destination == substation
        ) <= 1

    model.farm_limit = pyo.Constraint(model.farms, rule=farm_limit_rule)
    model.substation_limit = pyo.Constraint(
        model.substations, rule=substation_limit_rule
    )
    model.total_matches = pyo.Objective(
        expr=sum(
            model.x[farm, substation]
            for farm, substation in model.feasible_lines
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_matches))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}