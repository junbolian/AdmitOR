import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_centers = int(params["num_centers"])
    num_stores = int(params["num_stores"])

    centers = list(range(num_centers))
    stores = list(range(num_stores))

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.opens = pyo.Var(centers, domain=pyo.Binary)
    model.flow = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)

    model.opening_expr = pyo.Expression(
        expr=sum(opening_cost[i] * model.opens[i] for i in centers)
    )
    model.transport_expr = pyo.Expression(
        expr=sum(transport_cost[i][j] * model.flow[i, j]
                 for i in centers for j in stores)
    )
    model.total_cost = pyo.Objective(
        expr=model.opening_expr + model.transport_expr,
        sense=pyo.minimize
    )

    model.demand_con = pyo.Constraint(
        stores,
        rule=lambda m, j: sum(m.flow[i, j] for i in centers) == demand[j]
    )
    model.capacity_con = pyo.Constraint(
        centers,
        rule=lambda m, i: sum(m.flow[i, j] for j in stores)
        <= capacity[i] * m.opens[i]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}