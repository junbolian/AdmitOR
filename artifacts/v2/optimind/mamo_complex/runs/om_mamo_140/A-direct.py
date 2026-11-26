import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 9
    source = 0
    sink = 8

    # Directed arcs with capacity keys read from params
    arcs = []
    cap = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if i == sink:
                continue
            if j == source:
                continue
            key = "cap_{}_{}".format(i, j)
            if key in params:
                arcs.append((i, j))
                cap[(i, j)] = params[key]

    # Keep only arcs with positive capacity structure (0 arcs allowed but useless)
    arcs = [(i, j) for (i, j) in arcs if cap[(i, j)] > 0]

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    # Capacity constraints
    def cap_rule(model, i, j):
        return model.f[(i, j)] <= cap[(i, j)]
    model.cap_con = pyo.Constraint(model.A, rule=cap_rule)

    # Flow conservation for intermediate nodes (excluding source and sink)
    def cons_rule(model, k):
        inflow = sum(model.f[(i, j)] for (i, j) in arcs if j == k)
        outflow = sum(model.f[(i, j)] for (i, j) in arcs if i == k)
        return inflow - outflow == 0

    model.inter_nodes = pyo.Set(initialize=[k for k in range(n) if k != source and k != sink])
    model.flow_con = pyo.Constraint(model.inter_nodes, rule=cons_rule)

    # Objective: maximize net outflow from source (equals inflow to sink)
    def obj_rule(model):
        return sum(model.f[(i, j)] for (i, j) in arcs if i == source)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or solve failed"}