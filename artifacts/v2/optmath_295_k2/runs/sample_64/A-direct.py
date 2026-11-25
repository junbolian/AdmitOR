import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit_per_unit"]
    consumption = params["resource_consumption"]
    capacity = params["resource_capacity"]
    max_prod = params["max_production"]

    items = range(15)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.NonNegativeReals,
                      bounds=lambda m, i: (0, max_prod[i]))

    def resource_rule(m):
        return sum(consumption[i] * m.x[i] for i in items) <= capacity
    model.resource_limit = pyo.Constraint(rule=resource_rule)

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in items)
    model.profit_obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit_obj))
    return {"objective": obj_val, "status": "optimal"}