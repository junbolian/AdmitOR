import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    num_aircraft = len(availability)
    num_routes = len(demand)
    aircraft_index = range(num_aircraft)
    route_index = range(num_routes)

    model = pyo.ConcreteModel()

    model.aircraft = pyo.Set(initialize=list(aircraft_index))
    model.route = pyo.Set(initialize=list(route_index))

    model.assign = pyo.Var(model.aircraft, model.route, domain=pyo.NonNegativeIntegers)

    def obj_rule(m):
        return sum(cost[i][j] * m.assign[i, j] for i in m.aircraft for j in m.route)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def availability_rule(m, i):
        return sum(m.assign[i, j] for j in m.route) <= availability[i]

    model.availability_con = pyo.Constraint(model.aircraft, rule=availability_rule)

    def demand_rule(m, j):
        return sum(capacity[i][j] * m.assign[i, j] for i in m.aircraft) >= demand[j]

    model.demand_con = pyo.Constraint(model.route, rule=demand_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible"}