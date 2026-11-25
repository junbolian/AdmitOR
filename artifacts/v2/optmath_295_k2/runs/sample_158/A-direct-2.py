import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profit = params["profit"]

    num_companies = len(profit)
    num_markets = len(profit[0])
    num_products = len(profit[0][0])

    companies = range(num_companies)
    markets = range(num_markets)
    products = range(num_products)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(companies, markets, products, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(
            profit[c][mk][pr] * model.x[c, mk, pr]
            for c in companies
            for mk in markets
            for pr in products
        ),
        sense=pyo.maximize,
    )

    def demand_rule(m, mk, pr):
        return sum(m.x[c, mk, pr] for c in companies) == demand[mk][pr]

    model.demand_con = pyo.Constraint(markets, products, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}