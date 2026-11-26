import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_dcs = len(opening_cost)
    num_stores = len(demand)
    dcs = range(num_dcs)
    stores = range(num_stores)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(dcs, stores, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(dcs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(opening_cost[i] * model.y[i] for i in dcs)
        + sum(transport_cost[i][j] * model.x[i, j] for i in dcs for j in stores),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        stores,
        rule=lambda m, j: sum(m.x[i, j] for i in dcs) == demand[j],
    )

    model.capacity_con = pyo.Constraint(
        dcs,
        rule=lambda m, i: sum(m.x[i, j] for j in stores) <= capacity[i] * m.y[i],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}