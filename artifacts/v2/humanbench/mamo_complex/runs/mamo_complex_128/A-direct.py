import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    centers = list(range(1, 8))
    pairs = [(i, j) for i in centers for j in centers if i != j]

    # Build cost lookup from row-major ordered pairs (i,j), i!=j
    cost_map = {}
    k = 0
    for (i, j) in pairs:
        cost_map[(i, j)] = cost[k]
        k += 1

    model = pyo.ConcreteModel()
    model.x = pyo.Var(pairs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost_map[(i, j)] * m.x[(i, j)] for (i, j) in pairs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, c):
        outflow = sum(m.x[(c, j)] for j in centers if j != c)
        inflow = sum(m.x[(i, c)] for i in centers if i != c)
        return supply[c - 1] + inflow - outflow >= demand[c - 1]

    model.balance = pyo.Constraint(centers, rule=balance_rule)

    def supply_rule(m, c):
        return sum(m.x[(c, j)] for j in centers if j != c) <= supply[c - 1]

    model.outflow_limit = pyo.Constraint(centers, rule=supply_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}