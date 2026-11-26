import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]

    model = pyo.ConcreteModel()

    # Six 4-hour time blocks; a waiter working 8 hours starting at block i
    # covers blocks i and i+1 (mod 6).
    blocks = list(range(6))
    model.B = pyo.Set(initialize=blocks)

    # x[i] = number of waiters whose 8-hour shift starts at block i
    model.x = pyo.Var(model.B, domain=pyo.NonNegativeReals)

    # Coverage constraints: sum of shifts covering each block >= demand
    model.coverage = pyo.Constraint(model.B)

    def coverage_rule(m, j):
        return m.x[j] + m.x[(j - 1) % 6] >= demand[j]

    model.coverage_rule = pyo.Constraint(model.B, rule=coverage_rule)

    # Objective: total number of waiters = sum of all shift-start groups
    model.total = pyo.Objective(expr=sum(model.x[i] for i in model.B), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total))

    return {"objective": obj_val, "status": "optimal"}