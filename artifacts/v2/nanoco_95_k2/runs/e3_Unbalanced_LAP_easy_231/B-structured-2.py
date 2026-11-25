# IR: {"sets":{"staff":[0,1,2,3,4,5],"zones":[0,1,2,3,4,5]},"params":{"cost_matrix":"real[staff,zones], read from params['cost_matrix']"},"variables":{"assignment[staff,zones]":"binary"},"constraints":["For each staff member i: sum_j assignment[i,j] = 1","For each zone j: sum_i assignment[i,j] = 1"],"objective":"minimize sum_i sum_j cost_matrix[i,j] * assignment[i,j]"}

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
        initialize=lambda mdl, staff_idx, zone_idx: cost_matrix[staff_idx][zone_idx],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.staff,
        model.zones,
        domain=pyo.Binary,
    )

    def staff_assignment_rule(mdl, staff_idx):
        return sum(
            mdl.assignment[staff_idx, zone_idx] for zone_idx in mdl.zones
        ) == 1

    model.staff_assignment = pyo.Constraint(
        model.staff,
        rule=staff_assignment_rule,
    )

    def zone_coverage_rule(mdl, zone_idx):
        return sum(
            mdl.assignment[staff_idx, zone_idx] for staff_idx in mdl.staff
        ) == 1

    model.zone_coverage = pyo.Constraint(
        model.zones,
        rule=zone_coverage_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.deployment_cost[staff_idx, zone_idx]
            * model.assignment[staff_idx, zone_idx]
            for staff_idx in model.staff
            for zone_idx in model.zones
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