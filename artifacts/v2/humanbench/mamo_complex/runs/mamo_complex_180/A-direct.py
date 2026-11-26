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

    model.x_open = pyo.Var(centers, within=pyo.Binary)
    model.y_ship = pyo.Var(centers, stores, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(opening_cost[i] * model.x_open[i] for i in centers)
        + sum(transport_cost[i][j] * model.y_ship[i, j]
              for i in centers for j in stores),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        stores,
        rule=lambda m, j: sum(m.y_ship[i, j] for i in centers) == demand[j],
    )

    model.capacity_con = pyo.Constraint(
        centers,
        rule=lambda m, i: sum(m.y_ship[i, j] for j in stores)
        <= capacity[i] * m.x_open[i],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}