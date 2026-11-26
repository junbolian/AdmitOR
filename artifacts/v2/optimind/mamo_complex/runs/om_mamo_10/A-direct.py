import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_centers = len(opening_costs)
    n_stores = len(demands)
    centers = range(n_centers)
    stores = range(n_stores)

    model = pyo.ConcreteModel()

    model.y = pyo.Var(centers, within=pyo.Binary)
    model.x = pyo.Var(centers, stores, within=pyo.NonNegativeReals)

    model.c_demand = pyo.Constraint(
        stores,
        rule=lambda mb, j: sum(mb.x[i, j] for i in centers) == demands[j]
    )

    model.c_capacity = pyo.Constraint(
        centers,
        rule=lambda mb, i: sum(mb.x[i, j] for j in stores) <= capacities[i] * mb.y[i]
    )

    model.obj = pyo.Objective(
        expr=sum(opening_costs[i] * model.y[i] for i in centers)
        + sum(transport_costs[i][j] * model.x[i, j] for i in centers for j in stores),
        sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}