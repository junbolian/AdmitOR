import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profit_company0 = params["profit_company0"]
    profit_company1 = params["profit_company1"]

    n_markets = 4
    n_products = 3
    n_companies = 2

    markets = list(range(n_markets))
    products = list(range(n_products))
    companies = list(range(n_companies))

    profits = {0: profit_company0, 1: profit_company1}

    def profit_coef(c, mk, p):
        # market-major, product-minor indexing
        return profits[c][mk * n_products + p]

    def demand_val(mk, p):
        return demand[mk * n_products + p]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(companies, markets, products, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit_coef(c, mk, p) * m.x[c, mk, p]
            for c in companies
            for mk in markets
            for p in products
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    model.demand_con = pyo.Constraint(
        markets, products,
        rule=lambda m, mk, p: sum(m.x[c, mk, p] for c in companies) == demand_val(mk, p)
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}