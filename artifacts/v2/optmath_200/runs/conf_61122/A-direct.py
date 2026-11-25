import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    demand = params["demand"]
    profit = params["profit"]

    num_companies = 4
    num_markets = 5
    num_products = 2

    companies = range(num_companies)
    markets = range(num_markets)
    products = range(num_products)

    model = pyo.ConcreteModel()

    model.COMPANY = pyo.Set(initialize=list(companies))
    model.MARKET = pyo.Set(initialize=list(markets))
    model.PRODUCT = pyo.Set(initialize=list(products))

    model.x = pyo.Var(
        model.COMPANY, model.MARKET, model.PRODUCT,
        domain=pyo.NonNegativeReals, initialize=0.0
    )

    def profit_rule(model):
        return sum(
            profit[c][m][p] * model.x[c, m, p]
            for c in model.COMPANY
            for m in model.MARKET
            for p in model.PRODUCT
        )

    model.profit_expr = pyo.Expression(rule=profit_rule)
    model.obj = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def demand_rule(model, m, p):
        return sum(
            model.x[c, m, p] for c in model.COMPANY
        ) == demand[m][p]

    model.demand_con = pyo.Constraint(
        model.MARKET, model.PRODUCT, rule=demand_rule
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}