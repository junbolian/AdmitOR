import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capability = params["capability"]
    cost = params["cost"]

    n_aircraft = len(availability)
    n_routes = len(demand)

    model = pyo.ConcreteModel()

    # Use zero-based plain ranges (not RangeSet, which is 1-based)
    aircraft_idx = list(range(n_aircraft))
    route_idx = list(range(n_routes))

    model.x = pyo.Var(aircraft_idx, route_idx, domain=pyo.NonNegativeIntegers)

    def avail_rule(m, i):
        return sum(m.x[i, j] for j in route_idx) <= availability[i]
    model.avail_con = pyo.Constraint(aircraft_idx, rule=avail_rule)

    def demand_rule(m, j):
        return sum(capability[i][j] * m.x[i, j] for i in aircraft_idx) >= demand[j]
    model.demand_con = pyo.Constraint(route_idx, rule=demand_rule)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in aircraft_idx for j in route_idx),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or no solution found"}
    return {"objective": obj_val, "status": "optimal"}