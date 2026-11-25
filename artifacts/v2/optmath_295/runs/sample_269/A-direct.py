import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    consumption = params["resource_consumption"]
    capacity = params["resource_capacity"]
    upper = params["production_upper_limits"]

    n = len(profit)
    item_ids = list(range(n))

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_ids)

    model.x = pyo.Var(model.item_set, bounds=lambda m, i: (0, upper[i]))

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in m.item_set)

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def resource_rule(m):
        return sum(consumption[i] * m.x[i] for i in m.item_set) <= capacity

    model.resource_limit = pyo.Constraint(rule=resource_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}