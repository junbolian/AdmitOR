import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    item_names = [f"item_{i}" for i in range(13)]
    profits = params["profit"]
    rates = params["resource_rate"]
    capacities = params["production_capacity"]
    res_cap = params["resource_capacity"]

    model = pyo.ConcreteModel()

    model.ITEM = pyo.Set(initialize=item_names, ordered=True)

    def profit_rule(m, i):
        return profits[i]

    def rate_rule(m, i):
        return rates[i]

    def cap_rule(m, i):
        return capacities[i]

    model.profit = pyo.Param(model.ITEM, initialize=profit_rule)
    model.rate = pyo.Param(model.ITEM, initialize=rate_rule)
    model.cap = pyo.Param(model.ITEM, initialize=cap_rule)

    model.x = pyo.Var(model.ITEM, domain=pyo.NonNegativeReals,
                      bounds=lambda m, i: (0.0, m.cap[i]))

    def obj_rule(m):
        return sum(m.profit[i] * m.x[i] for i in m.ITEM)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def res_rule(m):
        return sum(m.rate[i] * m.x[i] for i in m.ITEM) <= res_cap

    model.resource_con = pyo.Constraint(rule=res_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}