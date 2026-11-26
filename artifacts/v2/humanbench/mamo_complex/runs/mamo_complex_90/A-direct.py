import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_centers = len(opening_cost)
    n_stores = len(demand)

    centers = list(range(n_centers))
    stores = list(range(n_stores))

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=centers, ordered=True)
    model.S = pyo.Set(initialize=stores, ordered=True)
    model.CS = pyo.Set(initialize=[(i, j) for i in centers for j in stores], dimen=2)

    model.open_dc = pyo.Var(model.C, domain=pyo.Binary)
    model.flow = pyo.Var(model.CS, domain=pyo.NonNegativeReals)

    model.total_cost = pyo.Objective(
        expr=sum(opening_cost[i] * model.open_dc[i] for i in model.C)
        + sum(transport_cost[i][j] * model.flow[i, j] for i in model.C for j in model.S),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        model.S,
        rule=lambda model, j: sum(model.flow[i, j] for i in model.C) == demand[j],
    )

    model.capacity_con = pyo.Constraint(
        model.C,
        rule=lambda model, i: sum(model.flow[i, j] for j in model.S)
        <= capacity[i] * model.open_dc[i],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}