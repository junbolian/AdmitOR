# IR: {"sets":{"staff":"0..14","shifts":"0..14"},"params":{"skill_scores":"params['skill_scores'], indexed by staff","shift_capacity":"params['shift_capacity']"},"variables":{"assigned[i,j]":"binary; staff i assigned to shift j","opened[j]":"binary; shift j opened"},"constraints":["For each i: sum_j assigned[i,j] = 1","For each i,j: assigned[i,j] <= opened[j]","For each j: sum_i skill_scores[i]*assigned[i,j] <= shift_capacity*opened[j]","For each j: opened[j] <= sum_i assigned[i,j]"],"objective":"minimize sum_j opened[j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    skill_scores = params["skill_scores"]
    shift_capacity = params["shift_capacity"]

    if len(skill_scores) != 15:
        raise ValueError("skill_scores must contain exactly 15 entries.")

    model = pyo.ConcreteModel()

    model.staff = pyo.Set(initialize=range(15), ordered=True)
    model.shifts = pyo.Set(initialize=range(15), ordered=True)

    model.skill = pyo.Param(
        model.staff,
        initialize={staff: skill_scores[staff] for staff in range(15)},
    )
    model.capacity = pyo.Param(initialize=shift_capacity)

    model.assigned = pyo.Var(
        model.staff, model.shifts, domain=pyo.Binary
    )
    model.opened = pyo.Var(model.shifts, domain=pyo.Binary)

    def assignment_rule(instance, staff):
        return sum(
            instance.assigned[staff, shift] for shift in instance.shifts
        ) == 1

    model.exactly_one_shift = pyo.Constraint(
        model.staff, rule=assignment_rule
    )

    def opening_link_rule(instance, staff, shift):
        return instance.assigned[staff, shift] <= instance.opened[shift]

    model.opening_link = pyo.Constraint(
        model.staff, model.shifts, rule=opening_link_rule
    )

    def capacity_rule(instance, shift):
        return sum(
            instance.skill[staff] * instance.assigned[staff, shift]
            for staff in instance.staff
        ) <= instance.capacity * instance.opened[shift]

    model.shift_load_limit = pyo.Constraint(
        model.shifts, rule=capacity_rule
    )

    def used_shift_rule(instance, shift):
        return instance.opened[shift] <= sum(
            instance.assigned[staff, shift] for staff in instance.staff
        )

    model.opened_shift_used = pyo.Constraint(
        model.shifts, rule=used_shift_rule
    )

    model.total_shifts = pyo.Objective(
        expr=sum(model.opened[shift] for shift in model.shifts),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when no feasible solution can be loaded.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_shifts))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}