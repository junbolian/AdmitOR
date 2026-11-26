import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_centers = 9
    n_stores = 5
    centers = range(n_centers)
    stores = range(n_stores)

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=centers)
    model.J = pyo.Set(initialize=stores)

    model.y = pyo.Var(model.I, domain=pyo.Binary)
    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    model.opening_expr = pyo.Expression(
        rule=lambda m: sum(opening_cost[i] * m.y[i] for i in m.I)
    )
    model.transport_expr = pyo.Expression(
        rule=lambda m: sum(transport_cost[i][j] * m.x[i, j] for i in m.I for j in m.J)
    )

    model.obj = pyo.Objective(
        expr=model.opening_expr + model.transport_expr, sense=pyo.minimize
    )

    model.demand_con = pyo.Constraint(
        model.J,
        rule=lambda m, j: sum(m.x[i, j] for i in m.I) == demand[j],
    )

    model.capacity_con = pyo.Constraint(
        model.I,
        rule=lambda m, i: sum(m.x[i, j] for j in m.J) <= capacity[i] * m.y[i],
    )

    try:
        Highs().solve(model)
    except Exception:
        return {"objective": None, "status": "solver failed"}

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "no feasible solution"}

    return {"objective": obj_val, "status": "optimal"}