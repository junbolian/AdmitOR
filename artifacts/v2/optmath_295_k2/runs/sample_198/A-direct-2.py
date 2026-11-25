import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margin = params["profit_margin"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    n_items = len(profit_margin)
    item_list = list(range(n_items))

    model = pyo.ConcreteModel()

    model.item_set = pyo.Set(initialize=item_list)

    model.produce = pyo.Var(model.item_set, within=pyo.NonNegativeReals)

    def profit_rule(m):
        return sum(profit_margin[i] * m.produce[i] for i in m.item_set)

    model.total_profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def capacity_rule(m):
        return sum(resource_consumption[i] * m.produce[i] for i in m.item_set) <= resource_capacity

    model.capacity_constraint = pyo.Constraint(rule=capacity_rule)

    def limit_rule(m, i):
        return m.produce[i] <= production_limit[i]

    model.limit_constraint = pyo.Constraint(model.item_set, rule=limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}