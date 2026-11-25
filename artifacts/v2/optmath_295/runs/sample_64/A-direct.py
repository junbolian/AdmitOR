import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_limits = params["production_limits"]

    n = len(profit)
    items = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.NonNegativeReals)

    def profit_rule(m):
        return sum(profit[i] * m.x[i] for i in items)

    model.total_profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def resource_rule(m):
        return sum(resource_consumption[i] * m.x[i] for i in items) <= resource_capacity

    model.resource_constraint = pyo.Constraint(rule=resource_rule)

    def limit_rule(m, i):
        return m.x[i] <= production_limits[i]

    model.limit_constraint = pyo.Constraint(items, rule=limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}