import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    regular_wage = params["regular_wage"]
    contract_wage = params["contract_wage"]
    shift_hours = params["shift_hours"]
    num_periods = params["num_periods"]
    num_shift_starts = params["num_shift_starts"]

    # Number of 4-hour periods covered per shift (frozen structural value)
    periods_per_shift = int(shift_hours // 4)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_periods - 1)
    model.S = pyo.RangeSet(0, num_shift_starts - 1)

    model.x = pyo.Var(model.S, domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var(model.S, domain=pyo.NonNegativeIntegers)

    shift_cost = shift_hours * (regular_wage + contract_wage)

    def obj_rule(m):
        return sum(m.x[s] * shift_hours * regular_wage + m.y[s] * shift_hours * contract_wage
                   for s in m.S)

    model.cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cover_rule(m, p):
        return sum(m.x[s] + m.y[s]
                   for s in m.S
                   if 0 <= (p - s) % num_periods < periods_per_shift) >= demand[p]

    model.cover = pyo.Constraint(model.P, rule=cover_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}