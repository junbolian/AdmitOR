import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]
    capacities = params["capacities"]
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]

    n_aircraft = len(aircraft_availability)
    n_routes = len(route_demand)
    aircraft_idx = range(n_aircraft)
    route_idx = range(n_routes)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(aircraft_idx, route_idx, domain=pyo.NonNegativeIntegers)

    model.aircraft_limit = pyo.Constraint(
        aircraft_idx,
        rule=lambda m, i: sum(m.x[i, j] for j in route_idx) <= aircraft_availability[i],
    )

    model.route_satisfy = pyo.Constraint(
        route_idx,
        rule=lambda m, j: sum(capacities[i][j] * m.x[i, j] for i in aircraft_idx) >= route_demand[j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(costs[i][j] * model.x[i, j] for i in aircraft_idx for j in route_idx),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}