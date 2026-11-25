import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist_flat = params["distance_matrix"]
    n = 7
    dist = [[dist_flat[i * n + j] for j in range(n)] for i in range(n)]

    edges = [(0, 1), (1, 3), (2, 6), (3, 4), (3, 5), (3, 6), (5, 6)]
    required = set()
    for (a, b) in edges:
        required.add((a, b))
        required.add((b, a))
    required = sorted(required)

    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    model.cost = pyo.Objective(
        expr=sum(dist[i][j] * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    # Mandatory sections must be traversed at least once
    def req_rule(model, i, j):
        return model.x[i, j] >= 1

    model.required_sections = pyo.Constraint(required, rule=req_rule)

    # Flow balance at every node (closed circuit)
    def balance_rule(model, k):
        outflow = sum(model.x[k, j] for j in range(n) if j != k)
        inflow = sum(model.x[i, k] for i in range(n) if i != k)
        return outflow == inflow

    model.balance = pyo.Constraint(range(n), rule=balance_rule)

    # Connectivity: ensure single closed tour (subtour elimination via cut set)
    # Since all degrees equal, enforce connectivity with cut constraints.
    nodes = list(range(n))
    subsets = []
    for mask in range(1, 1 << n):
        if mask == (1 << n) - 1:
            continue
        S = [v for v in nodes if mask & (1 << v)]
        if len(S) == 0 or len(S) == n:
            continue
        subsets.append(S)

    # Use only subsets containing node 0 to reduce and keep correctness
    # (cut for each proper subset not containing depot; equivalent to containing depot)
    cut_sets = []
    for S in subsets:
        if 0 in S:
            cut_sets.append(S)

    def cut_rule(model, idx):
        S = cut_sets[idx]
        Sset = set(S)
        return sum(model.x[i, j] for (i, j) in arcs if i in Sset and j not in Sset) >= 1

    model.cuts = pyo.Constraint(range(len(cut_sets)), rule=cut_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "infeasible_or_failed:" + str(type(exc).__name__)}