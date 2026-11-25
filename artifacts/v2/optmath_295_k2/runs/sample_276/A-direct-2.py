import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    n_aircraft = len(availability)
    n_routes = len(demand)

    model = pyo.ConcreteModel()

    model.AIRCRAFT = pyo.RangeSet(0, n_aircraft - 1)
    model.ROUTES = pyo.RangeSet(0, n_routes - 1)

    model.x = pyo.Var(model.AIRCRAFT, model.ROUTES, domain=pyo.NonNegativeIntegers)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.AIRCRAFT for j in m.ROUTES)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(capacity[i][j] * m.x[i, j] for i in m.AIRCRAFT) >= demand[j]

    model.demand_con = pyo.Constraint(model.ROUTES, rule=demand_rule)

    def avail_rule(m, i):
        return sum(m.x[i, j] for j in m.ROUTES) <= availability[i]

    model.avail_con = pyo.Constraint(model.AIRCRAFT, rule=avail_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}