import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Node sets
    N = list(range(9))          # all nodes: 0 = depot, 1..8 = clinics
    C = list(range(1, 9))       # clinic nodes
    K = list(range(params["num_vehicles"]))  # vehicles

    # Distance lookup: symmetric distances given as params dist_i_j for i<j
    dist = {}
    for i in N:
        dist[(i, i)] = 0.0
    for i in N:
        for j in N:
            if i < j:
                dist[(i, j)] = params[f"dist_{i}_{j}"]
                dist[(j, i)] = params[f"dist_{i}_{j}"]

    # Build model
    model = pyo.ConcreteModel()

    # Decision variables: x[k, i, j] = 1 if vehicle k travels directly from i to j
    model.x = pyo.Var(K, N, N, domain=pyo.Binary)

    # Objective: minimize total fleet distance
    def obj_rule(m):
        return sum(dist[(i, j)] * m.x[k, i, j] for k in K for i in N for j in N if i != j)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each clinic visited exactly once (in-degree and out-degree of 1 across vehicles)
    def visit_out_rule(m, j):
        return sum(m.x[k, i, j] for k in K for i in N if i != j) == 1

    model.visit_out = pyo.Constraint(C, rule=visit_out_rule)

    def visit_in_rule(m, i):
        return sum(m.x[k, i, j] for k in K for j in N if j != i) == 1

    model.visit_in = pyo.Constraint(C, rule=visit_in_rule)

    # Flow conservation at every node for each vehicle
    def flow_rule(m, k, i):
        return sum(m.x[k, i, j] for j in N if j != i) == sum(m.x[k, j, i] for j in N if j != i)

    model.flow = pyo.Constraint(K, N, rule=flow_rule)

    # Each vehicle departs depot at most once (and thus returns at most once)
    def depot_out_rule(m, k):
        return sum(m.x[k, 0, j] for j in N if j != 0) <= 1

    model.depot_out = pyo.Constraint(K, rule=depot_out_rule)

    # Subtour elimination (MTZ) within each vehicle route
    model.u = pyo.Var(K, C, bounds=(1, len(C)))

    def mtz_rule(m, k, i, j):
        if i != j:
            return m.u[k, i] - m.u[k, j] + len(C) * m.x[k, i, j] <= len(C) - 1
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(K, C, C, rule=mtz_rule)

    # Solve
    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}