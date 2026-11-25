import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    demand = params["demand"]

    companies = list(range(len(profit)))
    products = list(range(len(demand)))
    markets = list(range(len(demand[0])))

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=companies)
    model.P = pyo.Set(initialize=products)
    model.M = pyo.Set(initialize=markets)

    model.x = pyo.Var(model.C, model.P, model.M, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit[c][p][k] * m.x[c, p, k]
            for c in m.C for p in m.P for k in m.M
        )

    model.profit_expr = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(m, p, k):
        return sum(m.x[c, p, k] for c in m.C) == demand[p][k]

    model.demand_con = pyo.Constraint(model.P, model.M, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit_expr))
    return {"objective": obj_val, "status": "optimal"}