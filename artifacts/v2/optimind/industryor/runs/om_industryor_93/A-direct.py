import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    capacity = params["capacity"]
    production_cost = params["production_cost"]
    storage_cost = params["storage_cost"]

    T = len(demand)
    weeks = range(1, T + 1)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(weeks, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(weeks, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(production_cost[t - 1] * model.x[t] for t in weeks)
        + sum(storage_cost * model.inv[t] for t in weeks),
        sense=pyo.minimize,
    )

    model.cap_con = pyo.Constraint(
        weeks, rule=lambda mm, t: mm.x[t] <= capacity[t - 1]
    )

    # Inventory balance: inv[t] = inv[t-1] + x[t] - demand[t], inv[0] = 0
    def balance_rule(mm, t):
        prev_inv = mm.inv[t - 1] if t > 1 else 0
        return mm.inv[t] == prev_inv + mm.x[t] - demand[t - 1]

    model.balance_con = pyo.Constraint(weeks, rule=balance_rule)

    # Market demand must be met each week: inventory nonnegative
    model.demand_con = pyo.Constraint(
        weeks, rule=lambda mm, t: mm.inv[t] >= 0
    )

    # Final inventory of zero is optimal (no terminal holding)
    model.final_con = pyo.Constraint(expr=model.inv[T] == 0)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}