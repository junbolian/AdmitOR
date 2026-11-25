import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
    ]
    nodes = list(range(9))
    source = 0
    sink = 8

    def cname(i, j):
        return "cap_%d_%d" % (i, j)

    def costname(i, j):
        return "cost_%d_%d" % (i, j)

    cap = {(i, j): params[cname(i, j)] for (i, j) in arcs}
    cost = {(i, j): params[costname(i, j)] for (i, j) in arcs}

    model = pyo.ConcreteModel()
    model.ARC = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.ARC, domain=pyo.NonNegativeReals, bounds=lambda m, i, j: (0, cap[(i, j)]))

    def flow_balance_rule(m, k):
        inflow = sum(m.x[i, j] for (i, j) in arcs if j == k)
        outflow = sum(m.x[i, j] for (i, j) in arcs if i == k)
        if k == source:
            return outflow - inflow == m.F
        elif k == sink:
            return inflow - outflow == m.F
        else:
            return inflow - outflow == 0

    model.F = pyo.Var(domain=pyo.NonNegativeReals)
    model.balance = pyo.Constraint(nodes, rule=flow_balance_rule)

    model.total_cost = pyo.Expression(
        expr=sum(cost[(i, j)] * model.x[i, j] for (i, j) in arcs)
    )

    # Stage 1: maximize throughput
    model.obj1 = pyo.Objective(expr=model.F, sense=pyo.maximize)
    Highs().solve(model)
    fmax = float(pyo.value(model.F))

    # Fix max throughput
    model.throughput_fix = pyo.Constraint(expr=model.F >= fmax - 1e-6)

    # Stage 2: minimize cost
    model.obj1.deactivate()
    model.obj2 = pyo.Objective(expr=model.total_cost, sense=pyo.minimize)
    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}