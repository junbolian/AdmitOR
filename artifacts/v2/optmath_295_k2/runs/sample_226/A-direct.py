import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    companies = [0, 1, 2, 3]
    products = [0, 1]
    markets = [0, 1, 2, 3]

    # Demands read from params
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

    model.C = pyo.Set(initialize=companies)
    model.P = pyo.Set(initialize=products)
    model.M = pyo.Set(initialize=markets)

    model.x = pyo.Var(model.C, model.P, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            profit[c][p][mk] * mdl.x[c, p, mk]
            for c in companies
            for p in products
            for mk in markets
        )

    model.profit_total = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(mdl, p, mk):
        return sum(mdl.x[c, p, mk] for c in companies) == demand[(p, mk)]

    model.demand_con = pyo.Constraint(model.P, model.M, rule=demand_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.profit_total))
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}

    return {"objective": obj_val, "status": "optimal"}