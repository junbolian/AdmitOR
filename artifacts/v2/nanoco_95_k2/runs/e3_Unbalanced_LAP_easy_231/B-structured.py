# IR: {"sets":{"staff":[0,1,2,3,4,5],"zones":[0,1,2,3,4,5]},"params":{"cost_matrix":"6x6 real matrix supplied by params"},"variables":{"x[i,j]":"binary for each staff i and zone j"},"constraints":["For each staff i: sum_j x[i,j] = 1","For each zone j: sum_i x[i,j] = 1"],"objective":"Minimize sum_i sum_j cost_matrix[i][j] * x[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.staff = pyo.RangeSet(0, 5)
    model.zones = pyo.RangeSet(0, 5)

    model.deployment_cost = pyo.Param(
        model.staff,
        model.zones,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.staff, model.zones, domain=pyo.Binary)

    def staff_assignment_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.zones) == 1

    model.staff_assignment = pyo.Constraint(
        model.staff, rule=staff_assignment_rule
    )

    def zone_coverage_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.staff) == 1

    model.zone_coverage = pyo.Constraint(
        model.zones, rule=zone_coverage_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.deployment_cost[i, j] * model.x[i, j]
            for i in model.staff
            for j in model.zones
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}