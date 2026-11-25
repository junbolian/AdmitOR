import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    capacity = params["capacity"]
    operational_cost = params["operational_cost"]

    num_aircraft = len(aircraft_availability)
    num_routes = len(route_demand)

    model = pyo.ConcreteModel()

    model.AIRCRAFT = pyo.RangeSet(0, num_aircraft - 1)
    model.ROUTES = pyo.RangeSet(0, num_routes - 1)

    model.assign = pyo.Var(
        model.AIRCRAFT, model.ROUTES, domain=pyo.NonNegativeIntegers
    )

    def obj_rule(m):
        return sum(
            operational_cost[i][j] * m.assign[i, j]
            for i in m.AIRCRAFT
            for j in m.ROUTES
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def availability_rule(m, i):
        return sum(m.assign[i, j] for j in m.ROUTES) <= aircraft_availability[i]

    model.availability_constraint = pyo.Constraint(
        model.AIRCRAFT, rule=availability_rule
    )

    def demand_rule(m, j):
        return (
            sum(capacity[i][j] * m.assign[i, j] for i in m.AIRCRAFT)
            >= route_demand[j]
        )

    model.demand_constraint = pyo.Constraint(model.ROUTES, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}