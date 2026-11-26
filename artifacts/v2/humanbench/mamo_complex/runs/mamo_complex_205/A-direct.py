import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    price = params["security_price"]
    limit = params["share_limit"]
    payoff = params["payoff"]

    securities = list(range(5))
    countries = list(range(5))  # Argentina, Brazil, England, Spain, Germany

    model = pyo.ConcreteModel()

    model.x = pyo.Var(securities, domain=pyo.NonNegativeReals,
                      bounds=lambda m, i: (0, limit[i]))

    # Worst-case revenue over countries
    model.R = pyo.Var()

    def revenue_rule(m, c):
        return m.R <= sum(payoff[i][c] * m.x[i] for i in securities)

    model.revenue_con = pyo.Constraint(countries, rule=revenue_rule)

    # Budget: cost is exactly 1 (w.l.o.g. since revenue is linear & homogeneous)
    def budget_rule(m):
        return sum(price[i] * m.x[i] for i in securities) == 1

    model.budget = pyo.Constraint(rule=budget_rule)

    model.obj = pyo.Objective(expr=model.R, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}