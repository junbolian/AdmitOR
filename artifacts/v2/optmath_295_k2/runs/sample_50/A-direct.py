import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_aircraft = len(params["availability"])
    n_routes = len(params["route_demand"])

    aircraft = list(range(n_aircraft))
    routes = list(range(n_routes))

    availability = params["availability"]
    route_demand = params["route_demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.AC = pyo.Set(initialize=aircraft)
    model.RT = pyo.Set(initialize=routes)
    model.x = pyo.Var(model.AC, model.RT, domain=pyo.NonNegativeIntegers)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.AC for j in model.RT),
        sense=pyo.minimize,
    )

    model.avail_con = pyo.Constraint(
        model.AC,
        rule=lambda m, i: sum(m.x[i, j] for j in m.RT) <= availability[i],
    )

    model.demand_con = pyo.Constraint(
        model.RT,
        rule=lambda m, j: sum(capacity[i][j] * m.x[i, j] for i in m.AC) >= route_demand[j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}