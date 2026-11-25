import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()
    model.ORIG = pyo.RangeSet(0, n_orig - 1)
    model.DEST = pyo.RangeSet(0, n_dest - 1)

    model.x = pyo.Var(model.ORIG, model.DEST, domain=pyo.NonNegativeReals)

    model.supply_con = pyo.Constraint(
        model.ORIG,
        rule=lambda model_, i: sum(model.x[i, j] for j in model.DEST) == supply[i],
    )
    model.demand_con = pyo.Constraint(
        model.DEST,
        rule=lambda model_, j: sum(model.x[i, j] for i in model.ORIG) == demand[j],
    )
    model.cap_con = pyo.Constraint(
        model.ORIG,
        model.DEST,
        rule=lambda model_, i, j: model.x[i, j] <= capacity[i][j],
    )

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.ORIG for j in model.DEST),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}