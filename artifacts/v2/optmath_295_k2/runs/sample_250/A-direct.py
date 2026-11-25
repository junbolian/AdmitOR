import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_products = 6
    num_stages = 11
    products = list(range(num_products))
    stages = list(range(num_stages))

    profit = params["profit"]
    cap = params["stage_time_capacity"]
    coeff = params["stage_time_coeff"]
    min_commit = params["min_commitment"]
    demand = params["market_demand"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.S = pyo.Set(initialize=stages)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in m.P)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def stage_rule(m, s):
        return sum(coeff[s][i] * m.x[i] for i in m.P) <= cap[s]
    model.stage_limit = pyo.Constraint(model.S, rule=stage_rule)

    def lower_rule(m, i):
        return m.x[i] >= min_commit[i]
    model.min_req = pyo.Constraint(model.P, rule=lower_rule)

    def upper_rule(m, i):
        return m.x[i] <= demand[i]
    model.max_req = pyo.Constraint(model.P, rule=upper_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}