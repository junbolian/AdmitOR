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

    products = range(num_products)
    stages = range(num_stages)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(products, domain=pyo.NonNegativeReals)

    def objective_rule(m):
        return sum(profit[p] * m.x[p] for p in products)

    model.profit_total = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def stage_rule(m, s):
        return sum(stage_time[s][p] * m.x[p] for p in products) <= stage_capacity[s]

    model.stage_limit = pyo.Constraint(stages, rule=stage_rule)

    def min_rule(m, p):
        return m.x[p] >= min_commitment[p]

    model.min_commit = pyo.Constraint(products, rule=min_rule)

    def max_rule(m, p):
        return m.x[p] <= market_demand[p]

    model.max_demand = pyo.Constraint(products, rule=max_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit_total))
    return {"objective": obj_val, "status": "optimal"}