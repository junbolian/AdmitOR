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
    cap = {}
    cost = {}
    for (i, j) in arcs:
        cap[(i, j)] = params["cap_%d_%d" % (i, j)]
        cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    nodes = list(range(9))
    source = 0
    dest = 8

    # ---- Stage 1: maximize throughput ----
    model = pyo.ConcreteModel()
    model.ARC = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.ARC, domain=pyo.NonNegativeReals,
                      bounds=lambda m, i, j: (0, cap[(i, j)]))

    def flow_balance_rule(m, n):
        outflow = sum(m.x[i, j] for (i, j) in arcs if i == n)
        inflow = sum(m.x[i, j] for (i, j) in arcs if j == n)
        if n == source:
            return outflow - inflow == m.throughput
        elif n == dest:
            return inflow - outflow == m.throughput
        else:
            return outflow - inflow == 0

    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)
    model.balance = pyo.Constraint(nodes, rule=flow_balance_rule)

    model.obj1 = pyo.Objective(expr=model.throughput, sense=pyo.maximize)

    Highs().solve(model)
    max_throughput = float(pyo.value(model.throughput))

    # ---- Stage 2: minimize cost subject to throughput == max ----
    model2 = pyo.ConcreteModel()
    model2.ARC = pyo.Set(initialize=arcs, dimen=2)
    model2.x = pyo.Var(model2.ARC, domain=pyo.NonNegativeReals,
                       bounds=lambda m, i, j: (0, cap[(i, j)]))

    def flow_balance_rule2(m, n):
        outflow = sum(m.x[i, j] for (i, j) in arcs if i == n)
        inflow = sum(m.x[i, j] for (i, j) in arcs if j == n)
        if n == source:
            return outflow - inflow == max_throughput
        elif n == dest:
            return inflow - outflow == max_throughput
        else:
            return outflow - inflow == 0

    model2.balance = pyo.Constraint(nodes, rule=flow_balance_rule2)
    model2.obj2 = pyo.Objective(
        expr=sum(cost[(i, j)] * model2.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model2)
    obj_val = float(pyo.value(model2.obj2))

    return {"objective": obj_val, "status": "optimal"}