import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    companies = [0, 1, 2, 3]
    products = [0, 1]
    markets = [0, 1, 2]

    demand = {
        (0, 0): params["demand_p0_m0"], (1, 0): params["demand_p1_m0"],
        (0, 1): params["demand_p0_m1"], (1, 1): params["demand_p1_m1"],
        (0, 2): params["demand_p0_m2"], (1, 2): params["demand_p1_m2"],
    }

    profit = {}
    for c in companies:
        for p in products:
            for m in markets:
                profit[(c, p, m)] = params[f"profit_c{c}_p{p}_m{m}"]

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=companies, ordered=True)
    model.P = pyo.Set(initialize=products, ordered=True)
    model.M = pyo.Set(initialize=markets, ordered=True)

    model.x = pyo.Var(model.C, model.P, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[(c, p, mk)] * m.x[c, p, mk]
                   for c in companies for p in products for mk in markets)

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    model.demand_con = pyo.Constraint(
        model.P, model.M,
        rule=lambda m, p, mk: sum(m.x[c, p, mk] for c in companies) == demand[(p, mk)]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}