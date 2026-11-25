import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    capability = params["capability"]

    num_aircraft_types = 7
    num_routes = 7

    model = pyo.ConcreteModel()

    model.AIRCRAFT = pyo.RangeSet(0, num_aircraft_types - 1)
    model.ROUTE = pyo.RangeSet(0, num_routes - 1)

    model.x = pyo.Var(model.AIRCRAFT, model.ROUTE, domain=pyo.NonNegativeIntegers)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j]
                 for i in model.AIRCRAFT for j in model.ROUTE),
        sense=pyo.minimize,
    )

    def avail_rule(md, i):
        return sum(md.x[i, j] for j in md.ROUTE) <= availability[i]

    model.avail_con = pyo.Constraint(model.AIRCRAFT, rule=avail_rule)

    def demand_rule(md, j):
        return sum(capability[i][j] * md.x[i, j] for i in md.AIRCRAFT) >= demand[j]

    model.demand_con = pyo.Constraint(model.ROUTE, rule=demand_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}