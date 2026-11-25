# {"sets":{"I":"0,...,14 (staff)","J":"0,...,14 (candidate shifts)"},"params":{"skill_scores":"params['skill_scores'], indexed by I, nonnegative","max_skill_load_per_shift":"params['max_skill_load_per_shift'], nonnegative"},"variables":{"x[i,j]":"binary; staff i assigned to shift j","y[j]":"binary; shift j opened"},"constraints":["sum(x[i,j] for j in J) == 1 for each i in I","sum(skill_scores[i]*x[i,j] for i in I) <= max_skill_load_per_shift*y[j] for each j in J","x[i,j] <= y[j] for each i in I, j in J"],"objective":"minimize sum(y[j] for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    skill_scores = params["skill_scores"]
    max_skill_load_per_shift = params["max_skill_load_per_shift"]

    if len(skill_scores) != 15:
        raise ValueError("skill_scores must contain exactly 15 entries.")

    model = pyo.ConcreteModel()

    model.staff = pyo.RangeSet(0, 14)
    model.shifts = pyo.RangeSet(0, 14)

    model.skill_scores = pyo.Param(
        model.staff,
        initialize={i: skill_scores[i] for i in model.staff},
        within=pyo.NonNegativeReals,
    )
    model.max_skill_load_per_shift = pyo.Param(
        initialize=max_skill_load_per_shift,
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.staff, model.shifts, domain=pyo.Binary)
    model.y = pyo.Var(model.shifts, domain=pyo.Binary)

    def assignment_rule(mod, i):
        return sum(mod.x[i, j] for j in mod.shifts) == 1

    model.staff_assignment = pyo.Constraint(
        model.staff, rule=assignment_rule
    )

    def capacity_rule(mod, j):
        return (
            sum(mod.skill_scores[i] * mod.x[i, j] for i in mod.staff)
            <= mod.max_skill_load_per_shift * mod.y[j]
        )

    model.shift_capacity = pyo.Constraint(
        model.shifts, rule=capacity_rule
    )

    def opening_rule(mod, i, j):
        return mod.x[i, j] <= mod.y[j]

    model.assignment_requires_open_shift = pyo.Constraint(
        model.staff, model.shifts, rule=opening_rule
    )

    model.total_shifts = pyo.Objective(
        expr=sum(model.y[j] for j in model.shifts),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # HiGHS raises this when it cannot load a feasible solution.
        if "no solution can be loaded" in str(exc).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_shifts))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}