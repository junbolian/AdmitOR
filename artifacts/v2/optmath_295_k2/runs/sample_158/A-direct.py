import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profit = params["profit"]

    num_companies = 3
    num_markets = 4
    num_products = 2

    model = pyo.ConcreteModel()

    model.C = pyo.RangeSet(0, num_companies - 1)
    model.M = pyo.RangeSet(0, num_markets - 1)
    model.P = pyo.RangeSet(0, num_products - 1)

    model.x = pyo.Var(model.C, model.M, model.P, domain=pyo.NonNegativeReals)

    # profit is company-major, then market, product-minor:
    # profit -> list over companies, each a list over markets, each a list over products
    def obj_rule(m):
        return sum(
            profit[c][mk][p] * m.x[c, mk, p]
            for c in m.C for mk in m.M for p in m.P
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # demand is market-major, product-minor: demand[mk][p]
    def demand_rule(m, mk, p):
        return sum(m.x[c, mk, p] for c in m.C) == demand[mk][p]

    model.demand_con = pyo.Constraint(model.M, model.P, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}