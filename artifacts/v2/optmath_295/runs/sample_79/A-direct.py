import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_cost = params["transport_cost"]
    route_capacity = params["route_capacity"]

    n_warehouses = len(supplies)
    n_stores = len(demands)

    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, n_warehouses - 1)
    model.S = pyo.RangeSet(0, n_stores - 1)

    model.x = pyo.Var(model.W, model.S, within=pyo.NonNegativeReals)

    model.capacity_con = pyo.Constraint(
        model.W,
        model.S,
        rule=lambda m, i, j: m.x[i, j] <= route_capacity[i][j],
    )

    model.supply_con = pyo.Constraint(
        model.W,
        rule=lambda m, i: sum(m.x[i, j] for j in m.S) == supplies[i],
    )

    model.demand_con = pyo.Constraint(
        model.S,
        rule=lambda m, j: sum(m.x[i, j] for i in m.W) == demands[j],
    )

    model.obj = pyo.Objective(
        expr=sum(
            transport_cost[i][j] * model.x[i, j]
            for i in model.W
            for j in model.S
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}