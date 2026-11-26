import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    requirements = params["requirements"]
    shift_length = params["shift_length"]
    period_length = params["period_length"]

    n_shifts = len(requirements)
    covers = int(round(shift_length / period_length))

    model = pyo.ConcreteModel()
    model.shifts = pyo.RangeSet(0, n_shifts - 1)

    # x[i] = number of crew starting at beginning of shift i
    model.x = pyo.Var(model.shifts, domain=pyo.NonNegativeReals)

    # Each 4-hour period's requirement must be covered by all starts whose
    # 8-hour window (covering `covers` consecutive periods) overlaps it.
    def cover_rule(model, p):
        total = 0
        for i in range(n_shifts):
            covers_period = any((i + k) % n_shifts == p for k in range(covers))
            if covers_period:
                total = total + model.x[i]
        return total >= requirements[p]

    model.cover = pyo.Constraint(model.shifts, rule=cover_rule)

    model.obj = pyo.Objective(expr=sum(model.x[i] for i in model.shifts), sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "infeasible_or_failed"}