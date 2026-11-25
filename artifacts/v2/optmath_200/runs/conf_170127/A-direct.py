import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    n_aircraft = len(availability)
    n_routes = len(demand)

    aircraft_idx = list(range(n_aircraft))
    route_idx = list(range(n_routes))

    model = pyo.ConcreteModel()

    def x_bounds(mdl, i, j):
        return (0, availability[i])

    model.x = pyo.Var(
        aircraft_idx, route_idx, domain=pyo.NonNegativeIntegers, bounds=x_bounds
    )

    def avail_rule(mdl, i):
        return sum(mdl.x[i, j] for j in route_idx) <= availability[i]

    model.avail_con = pyo.Constraint(aircraft_idx, rule=avail_rule)

    def demand_rule(mdl, j):
        return sum(capacity[i][j] * mdl.x[i, j] for i in aircraft_idx) >= demand[j]

    model.demand_con = pyo.Constraint(route_idx, rule=demand_rule)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in aircraft_idx for j in route_idx)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}