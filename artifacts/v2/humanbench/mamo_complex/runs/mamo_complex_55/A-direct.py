import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    regions = [1, 2, 3, 4, 5]
    arcs = [(i, j) for i in regions for j in regions if i != j]

    cost = {}
    for (i, j) in arcs:
        cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    supply = {i: params["supply_%d" % i] for i in regions}
    demand = {i: params["demand_%d" % i] for i in regions}

    model = pyo.ConcreteModel()

    model.regions = pyo.Set(initialize=regions)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(md):
        return sum(cost[(i, j)] * md.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(md, r):
        inflow = sum(md.x[(i, r)] for i in regions if i != r)
        outflow = sum(md.x[(r, j)] for j in regions if j != r)
        return supply[r] + inflow - outflow == demand[r]

    model.balance = pyo.Constraint(model.regions, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}