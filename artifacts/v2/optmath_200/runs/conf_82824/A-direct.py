import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    suppliers = [0, 1, 2]
    products = [0, 1, 2]
    markets = [0, 1]

    demand = {
        0: params["demand_market0"],
        1: params["demand_market1"],
    }
    # profit[supplier][market][product]
    profit = {
        0: {
            0: params["profit_supplier0_market0"],
            1: params["profit_supplier0_market1"],
        },
        1: {
            0: params["profit_supplier1_market0"],
            1: params["profit_supplier1_market1"],
        },
        2: {
            0: params["profit_supplier2_market0"],
            1: params["profit_supplier2_market1"],
        },
    }

    model.sup = pyo.Set(initialize=suppliers)
    model.prod = pyo.Set(initialize=products)
    model.mkt = pyo.Set(initialize=markets)

    model.x = pyo.Var(model.sup, model.prod, model.mkt, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit[s][j][k] * m.x[s, k, j]
            for s in suppliers
            for k in products
            for j in markets
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    model.demand_con = pyo.ConstraintList()
    for j in markets:
        for k in products:
            model.demand_con.add(
                sum(model.x[s, k, j] for s in suppliers) == demand[j][k]
            )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}