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

    model.aircraft = pyo.RangeSet(0, n_aircraft - 1)
    model.routes = pyo.RangeSet(0, n_routes - 1)

    model.x = pyo.Var(model.aircraft, model.routes, within=pyo.NonNegativeIntegers)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.aircraft for j in m.routes)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def avail_rule(m, i):
        return sum(m.x[i, j] for j in m.routes) <= availability[i]

    model.availability_constraint = pyo.Constraint(model.aircraft, rule=avail_rule)

    def demand_rule(m, j):
        return sum(capability[i][j] * m.x[i, j] for i in m.aircraft) >= demand[j]

    model.demand_constraint = pyo.Constraint(model.routes, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}