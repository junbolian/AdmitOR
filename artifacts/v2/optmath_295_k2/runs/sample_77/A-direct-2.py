import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]
    capacities = params["capacities"]
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]

    n_aircraft = len(costs)
    n_routes = len(costs[0])

    aircrafts = list(range(n_aircraft))
    routes = list(range(n_routes))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(aircrafts, routes, domain=pyo.NonNegativeIntegers)

    model.obj = pyo.Objective(
        expr=sum(costs[i][j] * model.x[i, j] for i in aircrafts for j in routes),
        sense=pyo.minimize,
    )

    model.availability = pyo.Constraint(
        aircrafts,
        rule=lambda mo, i: sum(mo.x[i, j] for j in routes) <= aircraft_availability[i],
    )

    model.demand = pyo.Constraint(
        routes,
        rule=lambda mo, j: sum(
            capacities[i][j] * mo.x[i, j] for i in aircrafts
        ) >= route_demand[j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}