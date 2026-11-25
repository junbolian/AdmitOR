import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    capability = params["capability"]
    operational_cost = params["operational_cost"]

    num_aircraft = len(aircraft_availability)
    num_routes = len(route_demand)

    aircraft_idx = list(range(num_aircraft))
    route_idx = list(range(num_routes))

    model = pyo.ConcreteModel()
    model.A = pyo.Set(initialize=aircraft_idx)
    model.R = pyo.Set(initialize=route_idx)

    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    def cost_rule(m):
        return sum(operational_cost[a][r] * m.x[a, r] for a in m.A for r in m.R)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def avail_rule(m, a):
        return sum(m.x[a, r] for r in m.R) <= aircraft_availability[a]
    model.avail_con = pyo.Constraint(model.A, rule=avail_rule)

    def demand_rule(m, r):
        return sum(capability[a][r] * m.x[a, r] for a in m.A) >= route_demand[r]
    model.demand_con = pyo.Constraint(model.R, rule=demand_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}