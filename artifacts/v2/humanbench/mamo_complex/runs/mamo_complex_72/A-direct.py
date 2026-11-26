import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_centers = len(opening_cost)
    num_stores = len(demand)
    centers = range(num_centers)
    stores = range(num_stores)

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=list(centers))
    model.J = pyo.Set(initialize=list(stores))

    model.x = pyo.Var(model.I, model.J, within=pyo.NonNegativeReals)
    model.y = pyo.Var(model.I, within=pyo.Binary)

    model.open_cost_expr = pyo.Expression(
        expr=sum(opening_cost[i] * model.y[i] for i in model.I)
    )
    model.transport_expr = pyo.Expression(
        expr=sum(transport_cost[i][j] * model.x[i, j]
                 for i in model.I for j in model.J)
    )
    model.total_cost = pyo.Objective(
        expr=model.open_cost_expr + model.transport_expr,
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        model.J,
        rule=lambda m, j: sum(m.x[i, j] for i in m.I) == demand[j],
    )
    model.capacity_con = pyo.Constraint(
        model.I,
        rule=lambda m, i: sum(m.x[i, j] for j in m.J) <= capacity[i] * m.y[i],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}