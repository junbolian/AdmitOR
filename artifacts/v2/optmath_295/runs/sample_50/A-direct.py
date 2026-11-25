import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft = list(range(5))
    routes = list(range(7))

    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=aircraft)
    model.R = pyo.Set(initialize=routes)

    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.A for j in model.R),
        sense=pyo.minimize,
    )

    model.avail_con = pyo.Constraint(
        model.A,
        rule=lambda m, i: sum(m.x[i, j] for j in m.R) <= availability[i],
    )

    model.demand_con = pyo.Constraint(
        model.R,
        rule=lambda m, j: sum(capacity[i][j] * m.x[i, j] for i in m.A) >= demand[j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}