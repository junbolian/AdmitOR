import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    stage_capacity = params["stage_capacity"]
    stage_time = params["stage_time"]
    min_production = params["min_production"]
    max_demand = params["max_demand"]

    n_products = 6
    n_stages = 11
    products = list(range(n_products))
    stages = list(range(n_stages))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(products, domain=pyo.NonNegativeReals)

    def profit_rule(m):
        return sum(profit[p] * m.x[p] for p in products)

    model.total_profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def stage_rule(m, s):
        return sum(stage_time[s][p] * m.x[p] for p in products) <= stage_capacity[s]

    model.stage_limit = pyo.Constraint(stages, rule=stage_rule)

    def lower_rule(m, p):
        return m.x[p] >= min_production[p]

    model.lower_bound = pyo.Constraint(products, rule=lower_rule)

    def upper_rule(m, p):
        return m.x[p] <= max_demand[p]

    model.upper_bound = pyo.Constraint(products, rule=upper_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}