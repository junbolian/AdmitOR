import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margins = params["profit_margins"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_limits = params["production_limits"]

    n = len(profit_margins)
    item_idx = list(range(n))

    model = pyo.ConcreteModel()

    model.item_set = pyo.Set(initialize=item_idx)

    model.x = pyo.Var(model.item_set, domain=pyo.NonNegativeReals)

    def profit_rule(m):
        return sum(profit_margins[i] * m.x[i] for i in m.item_set)

    model.profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def resource_rule(m):
        return sum(resource_consumption[i] * m.x[i] for i in m.item_set) <= resource_capacity

    model.resource_constraint = pyo.Constraint(rule=resource_rule)

    def limit_rule(m, i):
        return m.x[i] <= production_limits[i]

    model.limit_constraint = pyo.Constraint(model.item_set, rule=limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}