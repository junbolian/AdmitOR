import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Nodes 0..8, source = 0, sink = 8
    nodes = list(range(9))

    # Build only arcs whose capacity is actually provided in params
    arcs = []
    cap_dict = {}
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            key = f"capacity_{i}_{j}"
            if key in params:
                arcs.append((i, j))
                cap_dict[(i, j)] = params[key]

    model = pyo.ConcreteModel()

    # Flow variables on each available directed arc
    model.FLOW = pyo.Var(arcs, domain=pyo.NonNegativeReals)

    # Capacity constraints
    def ub_rule(model, i, j):
        return model.FLOW[i, j] <= cap_dict[(i, j)]
    model.CAP = pyo.Constraint(arcs, rule=ub_rule)

    # Helper adjacency from arcs
    out_arcs = {n: [] for n in nodes}
    in_arcs = {n: [] for n in nodes}
    for (i, j) in arcs:
        out_arcs[i].append((i, j))
        in_arcs[j].append((i, j))

    # Flow conservation for intermediate nodes 1..7
    intermediate = [n for n in nodes if n not in (0, 8)]

    def cons_rule(model, n):
        inflow = sum(model.FLOW[i, j] for (i, j) in in_arcs[n])
        outflow = sum(model.FLOW[i, j] for (i, j) in out_arcs[n])
        return inflow == outflow
    model.CONS = pyo.Constraint(intermediate, rule=cons_rule)

    # Objective: maximize net flow from source (0) to sink (8)
    def obj_rule(model):
        out_src = sum(model.FLOW[i, j] for (i, j) in out_arcs[0])
        in_src = sum(model.FLOW[i, j] for (i, j) in in_arcs[0])
        return out_src - in_src
    model.OBJ = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.OBJ))
    return {'objective': obj_val, 'status': 'optimal'}