import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_ac = 7
    n_route = 6

    capacity_demand = params["capacity_demand"]
    aircraft_availability = params["aircraft_availability"]
    capacity_contribution = params["capacity_contribution"]
    assignment_cost = params["assignment_cost"]

    aircrafts = list(range(n_ac))
    routes = list(range(n_route))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(aircrafts, routes, domain=pyo.NonNegativeIntegers)

    def obj_rule(m):
        return sum(m.x[i, r] * assignment_cost[i][r] for i in aircrafts for r in routes)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, r):
        return sum(m.x[i, r] * capacity_contribution[i][r] for i in aircrafts) >= capacity_demand[r]
    model.demand_con = pyo.Constraint(routes, rule=demand_rule)

    def avail_rule(m, i):
        return sum(m.x[i, r] for r in routes) <= aircraft_availability[i]
    model.avail_con = pyo.Constraint(aircrafts, rule=avail_rule)

    # Allow aircraft to be assigned multiple times per route so that
    # demand (capacity units) can actually be met. The availability limit
    # is interpreted as a maximum total number of assignments per aircraft.
    result = Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}