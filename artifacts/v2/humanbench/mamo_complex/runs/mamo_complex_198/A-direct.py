import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    locations = [1, 2, 3, 4, 5]
    arcs = [(1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5), (3, 4), (3, 5), (4, 5)]

    cost = {}
    for (i, j) in arcs:
        cost[(i, j)] = params["cost_{}_{}".format(i, j)]

    supply = {i: params["supply_{}".format(i)] for i in locations}
    demand = {i: params["demand_{}".format(i)] for i in locations}

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(md):
        return sum(cost[(i, j)] * md.x[(i, j)] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Net flow balance per location: available (supply + inflow) - outflow >= demand
    # Since only one-directional arcs exist and total supply >= total demand, use >=.
    def balance_rule(md, k):
        inflow = sum(md.x[(i, j)] for (i, j) in arcs if j == k)
        outflow = sum(md.x[(i, j)] for (i, j) in arcs if i == k)
        return supply[k] + inflow - outflow >= demand[k]
    model.balance = pyo.Constraint(locations, rule=balance_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}