import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    companies = range(4)
    products = range(2)
    markets = range(4)

    demand = {
        (0, 0): params["demand_p0_m0"],
        (1, 0): params["demand_p1_m0"],
        (0, 1): params["demand_p0_m1"],
        (1, 1): params["demand_p1_m1"],
        (0, 2): params["demand_p0_m2"],
        (1, 2): params["demand_p1_m2"],
        (0, 3): params["demand_p0_m3"],
        (1, 3): params["demand_p1_m3"],
    }

    profit = params["profit"]

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=list(companies))
    model.P = pyo.Set(initialize=list(products))
    model.M = pyo.Set(initialize=list(markets))

    model.x = pyo.Var(model.C, model.P, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit[c][p][k] * m.x[c, p, k]
            for c in m.C for p in m.P for k in m.M
        )

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(m, p, k):
        return sum(m.x[c, p, k] for c in m.C) == demand[(p, k)]

    model.demand_con = pyo.Constraint(model.P, model.M, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}