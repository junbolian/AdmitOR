import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capability = params["capability"]
    cost = params["cost"]

    n_aircraft = len(availability)
    n_routes = len(demand)

    aircraft_idx = list(range(n_aircraft))
    route_idx = list(range(n_routes))

    model = pyo.ConcreteModel()

    model.aircraft = pyo.Set(initialize=aircraft_idx)
    model.routes = pyo.Set(initialize=route_idx)

    model.x = pyo.Var(model.aircraft, model.routes, domain=pyo.NonNegativeIntegers)

    def cost_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in mdl.aircraft for j in mdl.routes)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def avail_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.routes) <= availability[i]

    model.avail_con = pyo.Constraint(model.aircraft, rule=avail_rule)

    def demand_rule(mdl, j):
        return sum(capability[i][j] * mdl.x[i, j] for i in mdl.aircraft) >= demand[j]

    model.demand_con = pyo.Constraint(model.routes, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}