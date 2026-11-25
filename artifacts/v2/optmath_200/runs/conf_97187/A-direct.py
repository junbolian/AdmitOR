import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    companies = [0, 1, 2]
    products = [0, 1]
    markets = [0, 1, 2, 3]

    demand = {
        (0, 0): params["demand_p0"][0],
        (0, 1): params["demand_p1"][0],
        (1, 0): params["demand_p0"][1],
        (1, 1): params["demand_p1"][1],
        (2, 0): params["demand_p0"][2],
        (2, 1): params["demand_p1"][2],
        (3, 0): params["demand_p0"][3],
        (3, 1): params["demand_p1"][3],
    }

    profit = {
        (0, 0): params["profit_company0_product0"],
        (0, 1): params["profit_company0_product1"],
        (1, 0): params["profit_company1_product0"],
        (1, 1): params["profit_company1_product1"],
        (2, 0): params["profit_company2_product0"],
        (2, 1): params["profit_company2_product1"],
    }

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=companies)
    model.P = pyo.Set(initialize=products)
    model.M = pyo.Set(initialize=markets)

    model.x = pyo.Var(model.C, model.P, model.M, domain=pyo.NonNegativeReals)

    model.profit_expr = pyo.Expression(
        expr=sum(
            profit[(c, p)][mkt] * model.x[c, p, mkt]
            for c in companies for p in products for mkt in markets
        )
    )

    def demand_rule(m, p, mkt):
        return sum(m.x[c, p, mkt] for c in m.C) == demand[(mkt, p)]

    model.demand_con = pyo.Constraint(model.P, model.M, rule=demand_rule)

    model.obj = pyo.Objective(expr=model.profit_expr, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}