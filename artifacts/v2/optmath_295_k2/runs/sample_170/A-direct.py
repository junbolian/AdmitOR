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

    model.A = pyo.Set(initialize=aircraft_idx)
    model.R = pyo.Set(initialize=route_idx)
    model.AR = pyo.Set(initialize=[(i, r) for i in aircraft_idx for r in route_idx], dimen=2)

    model.x = pyo.Var(model.AR, domain=pyo.NonNegativeIntegers)

    def aircraft_limit_rule(model, i):
        return sum(model.x[i, r] for r in model.R) <= availability[i]

    model.aircraft_limit = pyo.Constraint(model.A, rule=aircraft_limit_rule)

    def route_demand_rule(model, r):
        return sum(capability[i][r] * model.x[i, r] for i in model.A) >= demand[r]

    model.route_demand = pyo.Constraint(model.R, rule=route_demand_rule)

    def objective_rule(model):
        return sum(cost[i][r] * model.x[i, r] for (i, r) in model.AR)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}