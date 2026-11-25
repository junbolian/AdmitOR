import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profit_data = [
        params["profit_supplier0"],
        params["profit_supplier1"],
        params["profit_supplier2"],
        params["profit_supplier3"],
    ]

    suppliers = range(4)
    regions = range(5)
    products = range(2)

    model = pyo.ConcreteModel()

    model.S = pyo.Set(initialize=list(suppliers))
    model.R = pyo.Set(initialize=list(regions))
    model.P = pyo.Set(initialize=list(products))

    model.x = pyo.Var(model.S, model.R, model.P, within=pyo.NonNegativeReals)

    profit = {}
    for s in suppliers:
        flat = profit_data[s]
        for r in regions:
            for p in products:
                profit[(s, r, p)] = flat[r * 2 + p]

    model.profit = pyo.Param(
        model.S, model.R, model.P,
        initialize=lambda m, s, r, p: profit[(s, r, p)],
        mutable=False,
    )

    model.obj = pyo.Objective(
        rule=lambda m: sum(m.profit[s, r, p] * m.x[s, r, p]
                           for s in m.S for r in m.R for p in m.P),
        sense=pyo.maximize,
    )

    demand_dict = {(r, p): demand[r][p] for r in regions for p in products}

    model.demand_con = pyo.Constraint(
        model.R, model.P,
        rule=lambda m, r, p: sum(m.x[s, r, p] for s in m.S) == demand_dict[(r, p)],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}