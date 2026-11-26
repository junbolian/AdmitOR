import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_centers = 5
    n_stores = 9
    centers = list(range(n_centers))
    stores = list(range(n_stores))

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(centers, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(opening_cost[i] * model.y[i] for i in centers)
        + sum(transport_cost[i][j] * model.x[i, j]
              for i in centers for j in stores),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        stores,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in centers) >= demand[j],
    )

    model.capacity_con = pyo.Constraint(
        centers,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in stores) <= capacity[i] * mdl.y[i],
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}