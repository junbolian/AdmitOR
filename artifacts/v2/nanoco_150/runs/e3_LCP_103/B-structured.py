# IR: {"sets":{"E":"{0,...,7}","A":"{(e,t): e in E, t in allowable_slots_exam[e]}","C":"{(i,j,t): (i,j) in conflict_pairs, (i,t) in A, (j,t) in A}"},"params":{"conflict_pairs":"params['conflict_pairs']","allowable_slots_exam[e]":"params['allowable_slots_exam0'] through params['allowable_slots_exam7']"},"variables":{"x[e,t]":"Binary for (e,t) in A","latest_slot":"Real"},"constraints":["For every e in E: sum(x[e,t] for allowable t) = 1","For every (i,j,t) in C: x[i,t] + x[j,t] <= 1","For every e in E: latest_slot >= sum(t*x[e,t] for allowable t)"],"objective":"Minimize latest_slot"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    allowable_slots = {
        0: tuple(dict.fromkeys(params["allowable_slots_exam0"])),
        1: tuple(dict.fromkeys(params["allowable_slots_exam1"])),
        2: tuple(dict.fromkeys(params["allowable_slots_exam2"])),
        3: tuple(dict.fromkeys(params["allowable_slots_exam3"])),
        4: tuple(dict.fromkeys(params["allowable_slots_exam4"])),
        5: tuple(dict.fromkeys(params["allowable_slots_exam5"])),
        6: tuple(dict.fromkeys(params["allowable_slots_exam6"])),
        7: tuple(dict.fromkeys(params["allowable_slots_exam7"])),
    }
    conflict_pairs = tuple(
        (first_exam, second_exam)
        for first_exam, second_exam in params["conflict_pairs"]
    )

    model = pyo.ConcreteModel()

    model.exams = pyo.RangeSet(0, 7)
    model.allowed_assignments = pyo.Set(
        dimen=2,
        initialize=[
            (exam, slot)
            for exam in range(8)
            for slot in allowable_slots[exam]
        ],
    )
    model.conflicting_assignments = pyo.Set(
        dimen=3,
        initialize=[
            (first_exam, second_exam, slot)
            for first_exam, second_exam in conflict_pairs
            for slot in allowable_slots[first_exam]
            if slot in allowable_slots[second_exam]
        ],
    )

    model.assignment = pyo.Var(
        model.allowed_assignments,
        domain=pyo.Binary,
    )
    model.latest_slot = pyo.Var(domain=pyo.Reals)

    def exactly_one_slot_rule(instance, exam):
        # Tuple form remains a valid constraint for an empty allowable list.
        return (
            1,
            pyo.quicksum(
                instance.assignment[exam, slot]
                for slot in allowable_slots[exam]
            ),
            1,
        )

    model.exactly_one_slot = pyo.Constraint(
        model.exams,
        rule=exactly_one_slot_rule,
    )

    def prevent_conflicts_rule(instance, first_exam, second_exam, slot):
        return (
            instance.assignment[first_exam, slot]
            + instance.assignment[second_exam, slot]
            <= 1
        )

    model.prevent_conflicts = pyo.Constraint(
        model.conflicting_assignments,
        rule=prevent_conflicts_rule,
    )

    def latest_slot_bound_rule(instance, exam):
        return instance.latest_slot >= pyo.quicksum(
            slot * instance.assignment[exam, slot]
            for slot in allowable_slots[exam]
        )

    model.latest_slot_bounds = pyo.Constraint(
        model.exams,
        rule=latest_slot_bound_rule,
    )

    model.schedule_objective = pyo.Objective(
        expr=model.latest_slot,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.schedule_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}