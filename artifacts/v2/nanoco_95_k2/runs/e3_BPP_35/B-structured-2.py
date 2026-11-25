# IR: {"sets":{"staff":"0..14","shifts":"0..14"},"params":{"skill_scores":"params['skill_scores'][i] for i in staff","max_skill_load_per_shift":"params['max_skill_load_per_shift']"},"variables":{"assigned[i,j]":"binary","opened[j]":"binary"},"constraints":["For each i: sum_j assigned[i,j] = 1","For each j: sum_i skill_scores[i]*assigned[i,j] <= max_skill_load_per_shift*opened[j]","For each i,j: assigned[i,j] <= opened[j]"],"objective":"minimize sum_j opened[j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    skill_scores = params["skill_scores"]
    max_skill_load_per_shift = params["max_skill_load_per_shift"]

    model = pyo.ConcreteModel()

    model.staff = pyo.RangeSet(0, 14)
    model.shifts = pyo.RangeSet(0, 14)

    model.skill_scores = pyo.Param(
        model.staff,
        initialize={staff_id: skill_scores[staff_id] for staff_id in model.staff},
        within=pyo.NonNegativeReals,
    )
    model.max_skill_load_per_shift = pyo.Param(
        initialize=max_skill_load_per_shift,
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(model.staff, model.shifts, domain=pyo.Binary)
    model.opened = pyo.Var(model.shifts, domain=pyo.Binary)

    def exactly_one_shift_rule(instance, staff_id):
        return sum(
            instance.assigned[staff_id, shift_id]
            for shift_id in instance.shifts
        ) == 1

    model.exactly_one_shift = pyo.Constraint(
        model.staff, rule=exactly_one_shift_rule
    )

    def shift_capacity_rule(instance, shift_id):
        return sum(
            instance.skill_scores[staff_id]
            * instance.assigned[staff_id, shift_id]
            for staff_id in instance.staff
        ) <= (
            instance.max_skill_load_per_shift * instance.opened[shift_id]
        )

    model.shift_capacity = pyo.Constraint(
        model.shifts, rule=shift_capacity_rule
    )

    def assignment_requires_open_shift_rule(instance, staff_id, shift_id):
        return (
            instance.assigned[staff_id, shift_id]
            <= instance.opened[shift_id]
        )

    model.assignment_requires_open_shift = pyo.Constraint(
        model.staff,
        model.shifts,
        rule=assignment_requires_open_shift_rule,
    )

    model.total_shifts = pyo.Objective(
        expr=sum(model.opened[shift_id] for shift_id in model.shifts),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_shifts))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}