import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    stage_capacity = params["stage_capacity"]
    min_commitment = params["min_commitment"]
    market_demand = params["market_demand"]
    stage_time = params["stage_time"]

    num_products = len(profit)
    num_stages = len(stage_capacity)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_products - 1)
    model.S = pyo.RangeSet(0, num_stages - 1)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals)

    def stage_rule(m, s):
        return sum(stage_time[s][p] * m.x[p] for p in m.P) <= stage_capacity[s]
    model.stage_limit = pyo.Constraint(model.S, rule=stage_rule)

    def min_rule(m, p):
        return m.x[p] >= min_commitment[p]
    model.min_commit = pyo.Constraint(model.P, rule=min_rule)

    def max_rule(m, p):
        return m.x[p] <= market_demand[p]
    model.max_demand = pyo.Constraint(model.P, rule=max_rule)

    def obj_rule(m):
        return sum(profit[p] * m.x[p] for p in m.P)
    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {'objective': obj_val, 'status': 'optimal'}