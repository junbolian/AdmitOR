import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    demand = params["demand"]

    n_companies = len(profit)
    n_markets = len(profit[0])

    model = pyo.ConcreteModel()
    model.i = pyo.RangeSet(0, n_companies - 1)
    model.j = pyo.RangeSet(0, n_markets - 1)

    model.x = pyo.Var(model.i, model.j, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(profit[i][j] * model.x[i, j]
                 for i in model.i for j in model.j),
        sense=pyo.maximize,
    )

    model.dem = pyo.Constraint(
        model.j,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in mdl.i) == demand[j],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}