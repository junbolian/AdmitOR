import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profit_c0 = params["profit_c0"]
    profit_c1 = params["profit_c1"]

    n_products = 3
    n_markets = 4
    companies = [0, 1]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_products - 1)
    model.M = pyo.RangeSet(0, n_markets - 1)
    model.C = pyo.RangeSet(0, len(companies) - 1)

    profit = {0: profit_c0, 1: profit_c1}

    model.x = pyo.Var(model.C, model.M, model.P, domain=pyo.NonNegativeReals)

    def profit_rule(mdl):
        return sum(
            profit[c][m][p] * mdl.x[c, m, p]
            for c in companies
            for m in range(n_markets)
            for p in range(n_products)
        )

    model.total_profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def demand_rule(mdl, m, p):
        return sum(mdl.x[c, m, p] for c in companies) == demand[m][p]

    model.demand_con = pyo.Constraint(model.M, model.P, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}