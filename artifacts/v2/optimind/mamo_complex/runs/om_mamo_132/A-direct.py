import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_centers = len(opening_cost)
    n_outlets = len(demand)
    centers = range(n_centers)
    outlets = range(n_outlets)

    model = pyo.ConcreteModel()

    model.x_open = pyo.Var(centers, domain=pyo.Binary)
    model.y_flow = pyo.Var(centers, outlets, domain=pyo.NonNegativeReals)

    model.transport_expr = pyo.Expression(
        rule=lambda m: sum(
            transport_cost[i][j] * m.y_flow[i, j]
            for i in centers for j in outlets
        )
    )
    model.opening_expr = pyo.Expression(
        rule=lambda m: sum(opening_cost[i] * m.x_open[i] for i in centers)
    )

    model.total_cost = pyo.Objective(
        expr=model.transport_expr + model.opening_expr,
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        outlets,
        rule=lambda m, j: sum(m.y_flow[i, j] for i in centers) == demand[j],
    )

    model.capacity_con = pyo.Constraint(
        centers,
        rule=lambda m, i: sum(m.y_flow[i, j] for j in outlets)
        <= capacity[i] * m.x_open[i],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}