import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profit = params["profit"]

    companies = range(5)
    products = range(3)
    markets = range(3)

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=list(companies))
    model.P = pyo.Set(initialize=list(products))
    model.M = pyo.Set(initialize=list(markets))

    model.x = pyo.Var(model.C, model.P, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            profit[c][p][mk] * mdl.x[c, p, mk]
            for c in mdl.C for p in mdl.P for mk in mdl.M
        )

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(mdl, p, mk):
        return sum(mdl.x[c, p, mk] for c in mdl.C) == demand[p][mk]

    model.demand_con = pyo.Constraint(model.P, model.M, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}