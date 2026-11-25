# IR: {"sets":{"staff":[0,1,2,3,4,5],"zones":[0,1,2,3,4,5]},"params":{"cost":{"source":"params['cost']","shape":[6,6],"type":"real"}},"variables":{"assignment[staff,zones]":"binary"},"constraints":["For each staff i: sum(assignment[i,j] for j in zones) == 1","For each zone j: sum(assignment[i,j] for i in staff) == 1"],"objective":{"sense":"minimize","expression":"sum(cost[i,j] * assignment[i,j] for i in staff for j in zones)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.staff = pyo.RangeSet(0, 5)
    model.zones = pyo.RangeSet(0, 5)

    model.deployment_cost = pyo.Param(
        model.staff,
        model.zones,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.staff,
        model.zones,
        domain=pyo.Binary,
    )

    model.staff_assignment = pyo.Constraint(
        model.staff,
        rule=lambda mdl, i: sum(
            mdl.assignment[i, j] for j in mdl.zones
        ) == 1,
    )

    model.zone_coverage = pyo.Constraint(
        model.zones,
        rule=lambda mdl, j: sum(
            mdl.assignment[i, j] for i in mdl.staff
        ) == 1,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.deployment_cost[i, j] * model.assignment[i, j]
            for i in model.staff
            for j in model.zones
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}