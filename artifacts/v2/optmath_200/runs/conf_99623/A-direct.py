import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit_per_unit"]
    resource = params["resource_consumption"]
    capacity = params["resource_capacity"]
    limit = params["production_limit"]

    n = len(profit)
    items = list(range(n))

    model = pyo.ConcreteModel()
    model.x = pyo.Var(items, domain=pyo.NonNegativeReals)

    def profit_rule(m):
        return sum(profit[i] * m.x[i] for i in items)

    def resource_rule(m):
        return sum(resource[i] * m.x[i] for i in items) <= capacity

    model.total_profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)
    model.resource_con = pyo.Constraint(rule=resource_rule)
    model.limits = pyo.Constraint(items, rule=lambda m, i: m.x[i] <= limit[i])

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_profit))
    except Exception:
        return {"objective": None, "status": "infeasible or unsolved"}

    return {"objective": obj_val, "status": "optimal"}