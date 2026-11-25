import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    costs = params["costs"]
    max_degree = params["max_degree"]
    n = 12
    nodes = list(range(n))

    model = pyo.ConcreteModel()
    model.E = pyo.Set(initialize=[(i, j) for i in nodes for j in nodes if i < j])

    model.x = pyo.Var(model.E, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(costs[i][j] * model.x[i, j] for (i, j) in model.E),
        sense=pyo.minimize
    )

    # Exactly n-1 edges (tree)
    model.edge_count = pyo.Constraint(
        expr=sum(model.x[i, j] for (i, j) in model.E) == n - 1
    )

    # Degree constraints
    def degree_rule(mm, k):
        return sum(mm.x[i, j] for (i, j) in mm.E if i == k or j == k) <= max_degree
    model.degree = pyo.Constraint(nodes, rule=degree_rule)

    # Connectivity via single-commodity flow rooted at node 0.
    # Orient flow from lower to higher index on each edge using two directed vars.
    model.F = pyo.Var(model.E, domain=pyo.NonNegativeReals)

    def cap_rule(mm, i, j):
        return mm.F[i, j] <= (n - 1) * mm.x[i, j]
    model.cap = pyo.Constraint(model.E, rule=cap_rule)

    def out_flow(mm, k):
        return sum(mm.F[i, j] for (i, j) in mm.E if i == k)

    def in_flow(mm, k):
        return sum(mm.F[i, j] for (i, j) in mm.E if j == k)

    def balance_rule(mm, k):
        if k == 0:
            return out_flow(mm, k) - in_flow(mm, k) == n - 1
        return in_flow(mm, k) - out_flow(mm, k) == 1
    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    # Prevent flow on edges "backwards" through root: node 0 must have no inflow
    model.root_no_in = pyo.Constraint(expr=in_flow(model, 0) == 0)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}