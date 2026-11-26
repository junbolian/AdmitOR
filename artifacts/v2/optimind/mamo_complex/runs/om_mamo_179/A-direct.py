import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Directed edges (i, j) with i != j for which a capacity parameter exists.
    edges = []
    for i in range(8):
        for j in range(8):
            if i == j:
                continue
            key = f"capacity_{i}_{j}"
            if key in params:
                edges.append((i, j))

    source = 0
    sink = 7

    model = pyo.ConcreteModel()
    model.edge_set = pyo.Set(initialize=edges, dimen=2)

    model.flow = pyo.Var(model.edge_set, domain=pyo.NonNegativeReals)

    capacity = {e: float(params[f"capacity_{e[0]}_{e[1]}"]) for e in edges}

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= capacity[(i, j)]

    model.capacity_con = pyo.Constraint(model.edge_set, rule=cap_rule)

    intermediates = [n for n in range(8) if n != source and n != sink]

    def flow_balance_rule(mdl, n):
        inflow = sum(mdl.flow[i, n] for (i, j) in edges if j == n)
        outflow = sum(mdl.flow[n, j] for (i, j) in edges if i == n)
        return inflow == outflow

    model.flow_balance = pyo.Constraint(intermediates, rule=flow_balance_rule)

    def obj_rule(mdl):
        return sum(mdl.flow[source, j] for (i, j) in edges if i == source)

    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_flow))
    return {'objective': obj_val, 'status': 'optimal'}