import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    route_demand = params["route_demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    n_aircraft = len(availability)
    n_routes = len(route_demand)

    aircraft_idx = list(range(n_aircraft))
    route_idx = list(range(n_routes))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(aircraft_idx, route_idx, domain=pyo.NonNegativeIntegers)

    def cost_rule(m):
        return sum(
            cost[i][j] * m.x[i, j]
            for i in aircraft_idx
            for j in route_idx
        )

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def avail_rule(m, i):
        return sum(m.x[i, j] for j in route_idx) <= availability[i]

    model.avail_con = pyo.Constraint(aircraft_idx, rule=avail_rule)

    def demand_rule(m, j):
        return sum(capacity[i][j] * m.x[i, j] for i in aircraft_idx) >= route_demand[j]

    model.demand_con = pyo.Constraint(route_idx, rule=demand_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": str(exc)[:100] or "solve failed"}