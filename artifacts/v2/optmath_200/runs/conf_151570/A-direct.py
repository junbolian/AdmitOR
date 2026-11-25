import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    stage_capacity = params["stage_capacity"]
    stage_time = params["stage_time"]
    min_production = params["min_production"]
    demand_limit = params["demand_limit"]

    n_products = len(profit)
    n_stages = len(stage_capacity)

    model = pyo.ConcreteModel()

    model.PRODUCTS = pyo.RangeSet(0, n_products - 1)
    model.STAGES = pyo.RangeSet(0, n_stages - 1)

    model.x = pyo.Var(model.PRODUCTS, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in m.PRODUCTS)

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def stage_rule(m, j):
        return sum(stage_time[j][i] * m.x[i] for i in m.PRODUCTS) <= stage_capacity[j]

    model.stage_limits = pyo.Constraint(model.STAGES, rule=stage_rule)

    def min_rule(m, i):
        return m.x[i] >= min_production[i]

    model.min_commit = pyo.Constraint(model.PRODUCTS, rule=min_rule)

    def max_rule(m, i):
        return m.x[i] <= demand_limit[i]

    model.max_demand = pyo.Constraint(model.PRODUCTS, rule=max_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}