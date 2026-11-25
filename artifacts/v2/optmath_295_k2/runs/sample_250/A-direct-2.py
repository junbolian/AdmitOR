import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    stage_time_capacity = params["stage_time_capacity"]
    stage_time_coeff = params["stage_time_coeff"]
    min_commitment = params["min_commitment"]
    market_demand = params["market_demand"]

    num_products = 6
    num_stages = 11

    model = pyo.ConcreteModel()

    model.PRODUCTS = pyo.RangeSet(0, num_products - 1)
    model.STAGES = pyo.RangeSet(0, num_stages - 1)

    def prod_bounds(m, p):
        return (min_commitment[p], market_demand[p])

    model.production = pyo.Var(model.PRODUCTS, bounds=prod_bounds)

    def obj_rule(m):
        return sum(profit[p] * m.production[p] for p in m.PRODUCTS)

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def stage_time_rule(m, s):
        return sum(stage_time_coeff[s][p] * m.production[p] for p in m.PRODUCTS) <= stage_time_capacity[s]

    model.stage_time_limit = pyo.Constraint(model.STAGES, rule=stage_time_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}