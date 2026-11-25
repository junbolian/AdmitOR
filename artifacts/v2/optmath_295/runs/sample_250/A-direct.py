import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    stage_capacity = params["stage_capacity"]
    stage_time = params["stage_time"]
    min_production = params["min_production"]
    max_demand = params["max_demand"]

    n_products = len(profit)
    n_stages = len(stage_capacity)

    products = list(range(n_products))
    stages = list(range(n_stages))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.S = pyo.Set(initialize=stages)

    model.x = pyo.Var(model.P, within=pyo.NonNegativeReals,
                      bounds=lambda m, p: (min_production[p], max_demand[p]))

    def profit_rule(m):
        return sum(profit[p] * m.x[p] for p in m.P)
    model.obj = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def stage_rule(m, s):
        return sum(stage_time[s * n_products + p] * m.x[p] for p in m.P) <= stage_capacity[s]
    model.stage_limit = pyo.Constraint(model.S, rule=stage_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}