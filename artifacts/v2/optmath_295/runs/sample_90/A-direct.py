import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n = len(supply)
    m = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n - 1)
    model.destinations = pyo.RangeSet(0, m - 1)

    model.x = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
        bounds=lambda md, i, j: (0, capacity[i][j]),
    )

    def supply_con(md, i):
        return sum(md.x[i, j] for j in md.destinations) == supply[i]

    def demand_con(md, j):
        return sum(md.x[i, j] for i in md.origins) == demand[j]

    model.supply_con = pyo.Constraint(model.origins, rule=supply_con)
    model.demand_con = pyo.Constraint(model.destinations, rule=demand_con)

    def total_cost(md):
        return sum(cost[i][j] * md.x[i, j] for i in md.origins for j in md.destinations)

    model.obj = pyo.Objective(rule=total_cost, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}