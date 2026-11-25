import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = len(supply)
    m = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n - 1)
    model.dests = pyo.RangeSet(0, m - 1)

    model.x = pyo.Var(model.origins, model.dests, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            transport_cost[i][j] * mdl.x[i, j]
            for i in mdl.origins
            for j in mdl.dests
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.dests) == supply[i]

    model.supply_constraint = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.origins) == demand[j]

    model.demand_constraint = pyo.Constraint(model.dests, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}