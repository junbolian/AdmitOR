import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    regions = [1, 2, 3, 4, 5, 6]

    stock = {i: params[f"stock_{i}"] if f"stock_{i}" in params else params["stock"][i-1] for i in regions}
    demand = {i: params[f"demand_{i}"] if f"demand_{i}" in params else params["demand"][i-1] for i in regions}

    cost = {}
    for i in regions:
        for j in regions:
            if i != j:
                cost[(i, j)] = params[f"cost_{i}_{j}"]

    model = pyo.ConcreteModel()
    model.regions = pyo.Set(initialize=regions)
    model.arcs = pyo.Set(initialize=[(i, j) for i in regions for j in regions if i != j])

    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in m.arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, i):
        outflow = sum(m.x[(i, j)] for j in regions if j != i)
        inflow = sum(m.x[(j, i)] for j in regions if j != i)
        return stock[i] - outflow + inflow == demand[i]
    model.balance = pyo.Constraint(model.regions, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}