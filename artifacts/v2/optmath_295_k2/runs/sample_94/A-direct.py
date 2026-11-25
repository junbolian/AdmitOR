import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profit = params["profit"]

    num_company = len(profit)
    num_product = len(profit[0])
    num_market = len(profit[0][0])

    model = pyo.ConcreteModel()

    model.C = pyo.RangeSet(num_company)
    model.P = pyo.RangeSet(num_product)
    model.M = pyo.RangeSet(num_market)

    model.x = pyo.Var(model.C, model.P, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit[c][p][k] * m.x[c, p, k]
            for c in m.C for p in m.P for k in m.M
        )
    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(m, p, k):
        return sum(m.x[c, p, k] for c in m.C) == demand[k][p]
    model.demand_con = pyo.Constraint(model.P, model.M, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}