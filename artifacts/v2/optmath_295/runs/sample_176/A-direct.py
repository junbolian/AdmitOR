import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_aircraft = len(availability)
    n_routes = len(demand)
    aircraft_idx = list(range(n_aircraft))
    route_idx = list(range(n_routes))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(aircraft_idx, route_idx, domain=pyo.NonNegativeIntegers)

    def obj_rule(mod):
        return sum(cost[i][r] * mod.x[i, r] for i in aircraft_idx for r in route_idx)

    model.obj_expr = pyo.Expression(rule=obj_rule)

    def avail_rule(mod, i):
        return sum(mod.x[i, r] for r in route_idx) <= availability[i]

    model.avail_con = pyo.Constraint(aircraft_idx, rule=avail_rule)

    def demand_rule(mod, r):
        return sum(capacity[i][r] * mod.x[i, r] for i in aircraft_idx) >= demand[r]

    model.demand_con = pyo.Constraint(route_idx, rule=demand_rule)

    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.objective))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}