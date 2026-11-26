import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    regions = [1, 2, 3, 4, 5, 6]

    supply = {i: params["supply"][i - 1] for i in regions}
    demand = {i: params["demand"][i - 1] for i in regions}

    cost = {}
    for i in regions:
        for j in regions:
            if i != j:
                cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=[(i, j) for i in regions for j in regions if i != j])

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.flow[(i, j)] for (i, j) in m.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, i):
        inflow = sum(m.flow[(j, i)] for j in regions if j != i)
        outflow = sum(m.flow[(i, j)] for j in regions if j != i)
        return supply[i] + inflow - outflow >= demand[i]

    model.balance = pyo.Constraint(regions, rule=balance_rule)

    def out_rule(m, i):
        return sum(m.flow[(i, j)] for j in regions if j != i) <= supply[i]

    model.outflow = pyo.Constraint(regions, rule=out_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}