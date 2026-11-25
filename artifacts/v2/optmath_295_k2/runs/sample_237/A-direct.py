import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    demand = params["demand"]

    n_companies = len(profit)
    n_markets = len(profit[0])
    n_products = len(profit[0][0])

    model = pyo.ConcreteModel()

    model.COMPANIES = pyo.RangeSet(0, n_companies - 1)
    model.MARKETS = pyo.RangeSet(0, n_markets - 1)
    model.PRODUCTS = pyo.RangeSet(0, n_products - 1)

    model.x = pyo.Var(
        model.COMPANIES, model.MARKETS, model.PRODUCTS,
        domain=pyo.NonNegativeReals,
    )

    def obj_rule(m):
        return sum(
            profit[c][k][p] * m.x[c, k, p]
            for c in m.COMPANIES
            for k in m.MARKETS
            for p in m.PRODUCTS
        )

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(m, k, p):
        return sum(m.x[c, k, p] for c in m.COMPANIES) == demand[k][p]

    model.demand_con = pyo.Constraint(
        model.MARKETS, model.PRODUCTS, rule=demand_rule
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}