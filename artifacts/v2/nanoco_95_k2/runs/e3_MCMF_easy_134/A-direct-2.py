import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    arcs = [
        (0, 1), (1, 2), (1, 4), (1, 5), (1, 7),
        (2, 3), (3, 4), (4, 5), (4, 8), (4, 9),
        (5, 6), (5, 7), (6, 7), (7, 8), (8, 9),
    ]
    nodes = list(range(10))
    source, sink = 0, 9

    cap = {a: params["capacity_%d_%d" % a] for a in arcs}
    cst = {a: params["cost_%d_%d" % a] for a in arcs}

    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.FLOW = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def cap_rule(md, i, j):
        return md.FLOW[i, j] <= cap[(i, j)]
    model.CAP = pyo.Constraint(model.ARCS, rule=cap_rule)

    def bal_rule(md, n):
        inflow = sum(md.FLOW[i, j] for (i, j) in arcs if j == n)
        outflow = sum(md.FLOW[i, j] for (i, j) in arcs if i == n)
        if n == source:
            return outflow - inflow >= 0
        elif n == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0
    model.BAL = pyo.Constraint(nodes, rule=bal_rule)

    # Stage 1: maximize flow out of source (equivalently into sink)
    def obj1_rule(md):
        return sum(md.FLOW[source, j] for (i, j) in arcs if i == source)
    model.OBJ1 = pyo.Objective(rule=obj1_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj1_val = float(pyo.value(model.OBJ1))

    # Stage 2: fix max flow, minimize cost
    model.OBJ1.deactivate()

    def fix_rule(md):
        return sum(md.FLOW[source, j] for (i, j) in arcs if i == source) >= obj1_val - 1e-7
    model.FIXFLOW = pyo.Constraint(rule=fix_rule)

    def obj2_rule(md):
        return sum(cst[(i, j)] * md.FLOW[i, j] for (i, j) in arcs)
    model.OBJ2 = pyo.Objective(rule=obj2_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.OBJ2))
    return {"objective": obj_val, "status": "optimal"}