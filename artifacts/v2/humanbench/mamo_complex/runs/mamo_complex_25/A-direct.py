import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_centers = 8
    n_stores = 5

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    centers = list(range(n_centers))
    stores = list(range(n_stores))

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=centers)
    model.J = pyo.Set(initialize=stores)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.I, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(opening_cost[i] * model.y[i] for i in model.I)
        + sum(transport_cost[i][j] * model.x[i, j]
              for i in model.I for j in model.J),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in mdl.I) == demand[j],
    )

    model.cap_con = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in mdl.J)
        <= capacity[i] * mdl.y[i],
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}