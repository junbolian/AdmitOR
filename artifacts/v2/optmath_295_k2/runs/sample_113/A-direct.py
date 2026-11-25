import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_usage = params["resource_usage"]
    capacity = params["capacity"]
    resource_budget = params["resource_budget"]

    n = len(profit)
    items = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.NonNegativeReals)

    def profit_rule(m):
        return sum(profit[i] * m.x[i] for i in items)

    model.total_profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def resource_rule(m):
        return sum(resource_usage[i] * m.x[i] for i in items) <= resource_budget

    model.resource_limit = pyo.Constraint(rule=resource_rule)

    model.cap_upper = pyo.Constraint(items, rule=lambda m, i: m.x[i] <= capacity[i])

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}