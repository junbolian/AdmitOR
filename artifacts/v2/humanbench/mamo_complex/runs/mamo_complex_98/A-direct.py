import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_centers = len(opening_cost)
    n_stores = len(demand)
    centers = range(n_centers)
    stores = range(n_stores)

    model = pyo.ConcreteModel()

    model.y = pyo.Var(centers, domain=pyo.Binary)
    model.x = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(opening_cost[i] * model.y[i] for i in centers)
        + sum(transport_cost[i][j] * model.x[i, j] for i in centers for j in stores),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        stores,
        rule=lambda model, j: sum(model.x[i, j] for i in centers) == demand[j],
    )

    model.capacity_con = pyo.Constraint(
        centers,
        rule=lambda model, i: sum(model.x[i, j] for j in stores) <= capacity[i] * model.y[i],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}