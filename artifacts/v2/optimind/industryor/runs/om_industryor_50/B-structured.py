# IR: {"sets":{"shifts":[1,2,3,4,5,6]},"params":{"req_shift1":"required staff in shift 1","req_shift2":"required staff in shift 2","req_shift3":"required staff in shift 3","req_shift4":"required staff in shift 4","req_shift5":"required staff in shift 5","req_shift6":"required staff in shift 6"},"variables":{"staff_start[s]":{"type":"nonnegative integer","index":"s in shifts","meaning":"staff starting an eight-hour work period in shift s"}},"constraints":["staff_start[1] + staff_start[6] >= req_shift1","staff_start[2] + staff_start[1] >= req_shift2","staff_start[3] + staff_start[2] >= req_shift3","staff_start[4] + staff_start[3] >= req_shift4","staff_start[5] + staff_start[4] >= req_shift5","staff_start[6] + staff_start[5] >= req_shift6"],"objective":{"sense":"minimize","expression":"sum(staff_start[s] for s in shifts)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    requirements = {
        1: params["req_shift1"],
        2: params["req_shift2"],
        3: params["req_shift3"],
        4: params["req_shift4"],
        5: params["req_shift5"],
        6: params["req_shift6"],
    }

    model = pyo.ConcreteModel()
    model.shifts = pyo.RangeSet(1, 6)
    model.required_staff = pyo.Param(
        model.shifts,
        initialize=requirements,
        within=pyo.NonNegativeReals,
    )
    model.staff_start = pyo.Var(
        model.shifts,
        domain=pyo.NonNegativeIntegers,
    )

    # Each eight-hour work period covers two consecutive four-hour shifts.
    # Shift 6 continues into shift 1 of the following daily cycle.
    def coverage_rule(instance, shift):
        previous_shift = 6 if shift == 1 else shift - 1
        return (
            instance.staff_start[shift]
            + instance.staff_start[previous_shift]
            >= instance.required_staff[shift]
        )

    model.coverage = pyo.Constraint(model.shifts, rule=coverage_rule)
    model.total_staff = pyo.Objective(
        expr=sum(model.staff_start[shift] for shift in model.shifts),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_staff))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}