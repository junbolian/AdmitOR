import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    arcs = [
        (0, 1), (0, 6), (0, 8),
        (1, 2),
        (2, 3), (2, 7),
        (3, 4),
        (4, 5), (4, 7), (4, 8),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
        (8, 9),
    ]
    nodes = list(range(10))
    source = 0
    sink = 9

    model = pyo.ConcreteModel()

    model.arc_set = pyo.Set(initialize=arcs, dimen=2)
    model.node_set = pyo.Set(initialize=nodes)

    caps = {}
    for (i, j) in arcs:
        caps[(i, j)] = params["capacity_%d_%d" % (i, j)]

    def cap_rule(mdl, i, j):
        return caps[(i, j)]

    model.cap = pyo.Param(model.arc_set, initialize=cap_rule, mutable=False)

    model.flow = pyo.Var(model.arc_set, domain=pyo.NonNegativeReals)

    def cap_constraint_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.cap[i, j]

    model.cap_constraint = pyo.Constraint(model.arc_set, rule=cap_constraint_rule)

    out_arcs = {n: [] for n in nodes}
    in_arcs = {n: [] for n in nodes}
    for (i, j) in arcs:
        out_arcs[i].append((i, j))
        in_arcs[j].append((i, j))

    def balance_rule(mdl, n):
        if n == source or n == sink:
            return pyo.Constraint.Skip
        inflow = sum(mdl.flow[i, j] for (i, j) in in_arcs[n])
        outflow = sum(mdl.flow[i, j] for (i, j) in out_arcs[n])
        return inflow == outflow

    model.flow_balance = pyo.Constraint(model.node_set, rule=balance_rule)

    def obj_rule(mdl):
        return sum(mdl.flow[i, j] for (i, j) in out_arcs[source])

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}