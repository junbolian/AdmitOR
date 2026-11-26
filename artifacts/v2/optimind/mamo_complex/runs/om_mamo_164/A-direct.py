import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    regions = [1, 2, 3, 4, 5]

    interactions = [(i, j) for i in regions for j in regions if i != j]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=interactions, dimen=2)

    def cost_rule(mdl, i, j):
        return params["cost_%d_%d" % (i, j)]

    model.transport_cost = pyo.Param(model.arcs, initialize=cost_rule)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(mdl.transport_cost[i, j] * mdl.flow[i, j] for (i, j) in mdl.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(mdl, k):
        inflow = sum(mdl.flow[i, k] for i in regions if i != k)
        outflow = sum(mdl.flow[k, j] for j in regions if j != k)
        return inflow - outflow == params["demand_%d" % k] - params["supply_%d" % k]

    model.balance = pyo.Constraint(regions, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}