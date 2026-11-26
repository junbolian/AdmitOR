import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]

    days = list(range(1, 8))

    model = pyo.ConcreteModel()
    model.D = pyo.Set(initialize=days)

    # x[j] = number of nurses starting their 5-day streak on day j
    model.x = pyo.Var(model.D, within=pyo.NonNegativeReals)

    # total nurses used
    model.total_nurses = pyo.Objective(
        expr=sum(model.x[j] for j in model.D), sense=pyo.minimize
    )

    # demand coverage: day d covered by shifts starting d, d-1, ..., d-4 (mod 7)
    def coverage_rule(m, d):
        return sum(m.x[((d - k - 1) % 7) + 1] for k in range(5)) >= demand[d - 1]

    model.coverage = pyo.Constraint(model.D, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_nurses))
    return {"objective": obj_val, "status": "optimal"}