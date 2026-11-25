import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n_orig - 1)
    model.destinations = pyo.RangeSet(0, n_dest - 1)

    model.ship = pyo.Var(model.origins, model.destinations, domain=pyo.NonNegativeReals)

    def obj_rule(md):
        return sum(cost[i][j] * md.ship[i, j] for i in md.origins for j in md.destinations)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(md, i):
        return sum(md.ship[i, j] for j in md.destinations) == supply[i]

    model.supply_constraint = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(md, j):
        return sum(md.ship[i, j] for i in md.origins) == demand[j]

    model.demand_constraint = pyo.Constraint(model.destinations, rule=demand_rule)

    def capacity_rule(md, i, j):
        return md.ship[i, j] <= capacity[i][j]

    model.capacity_constraint = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}