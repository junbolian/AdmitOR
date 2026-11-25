import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_w = len(supply)
    num_s = len(demand)
    warehouses = list(range(num_w))
    stores = list(range(num_s))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(warehouses, stores, domain=pyo.NonNegativeReals,
                      bounds=lambda m, i, j: (0, capacity[i][j]))

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in warehouses for j in stores),
        sense=pyo.minimize,
    )

    model.supply_constraint = pyo.Constraint(
        warehouses,
        rule=lambda m, i: sum(m.x[i, j] for j in stores) == supply[i],
    )

    model.demand_constraint = pyo.Constraint(
        stores,
        rule=lambda m, j: sum(m.x[i, j] for i in warehouses) == demand[j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}