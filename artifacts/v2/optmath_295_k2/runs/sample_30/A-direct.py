import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 45
    items = list(range(n))

    profit = params["profit_per_unit"]
    consumption = params["resource_consumption_per_unit"]
    resource_avail = params["resource_availability"]
    prod_limit = params["production_limit"]

    model = pyo.ConcreteModel()

    model.Items = pyo.Set(initialize=items)

    model.x = pyo.Var(model.Items, domain=pyo.NonNegativeReals)

    def profit_rule(m):
        return sum(profit[i] * m.x[i] for i in m.Items)
    model.total_profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def resource_rule(m):
        return sum(consumption[i] * m.x[i] for i in m.Items) <= resource_avail
    model.resource_con = pyo.Constraint(rule=resource_rule)

    def limit_rule(m, i):
        return m.x[i] <= prod_limit[i]
    model.limit_con = pyo.Constraint(model.Items, rule=limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}