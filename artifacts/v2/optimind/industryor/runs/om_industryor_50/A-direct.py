import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    req = {
        1: params["req_shift1"],
        2: params["req_shift2"],
        3: params["req_shift3"],
        4: params["req_shift4"],
        5: params["req_shift5"],
        6: params["req_shift6"],
    }

    model = pyo.ConcreteModel()

    # x[i] = number of crews starting their shift at the beginning of period i
    model.SHIFTS = pyo.RangeSet(1, 6)
    model.x = pyo.Var(model.SHIFTS, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(m.x[i] for i in m.SHIFTS)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each 8-hour shift (starting at period i) covers periods i, i+1, i+2, i+3 (mod 6).
    # Coverage constraints: workers present in each period >= requirement.
    def coverage_rule(m, t):
        return sum(m.x[i] for i in m.SHIFTS if (t - i) % 6 in (0, 1, 2, 3)) >= req[t]

    model.coverage = pyo.Constraint(model.SHIFTS, rule=coverage_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible"}