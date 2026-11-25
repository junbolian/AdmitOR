import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel("transportation")

    model.origins = pyo.RangeSet(0, n_orig - 1)
    model.destinations = pyo.RangeSet(0, n_dest - 1)

    model.x = pyo.Var(model.origins, model.destinations, within=pyo.NonNegativeReals)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.destinations) == supply[i]
    model.supply_constraint = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.origins) == demand[j]
    model.demand_constraint = pyo.Constraint(model.destinations, rule=demand_rule)

    def total_cost_rule(m):
        return sum(cost[i][j] * m.x[i, j]
                   for i in m.origins for j in m.destinations)
    model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}