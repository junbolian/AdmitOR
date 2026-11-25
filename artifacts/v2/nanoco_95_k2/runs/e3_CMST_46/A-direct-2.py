import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = 16
    nodes = list(range(N))
    root = 0
    non_root = [i for i in nodes if i != root]
    port_limit = params["splitter_port_limit"]

    # Distance matrix from params
    dist = {}
    for i in range(N):
        for j in range(i + 1, N):
            key = "dist_{}_{}".format(i, j)
            dist[(i, j)] = params[key]
            dist[(j, i)] = params[key]

    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    bigM = N

    model = pyo.ConcreteModel()

    # x[i,j] = 1 if directed arc i->j (j is child of i)
    model.x = pyo.Var(arcs, domain=pyo.Binary)

    # z[i] = 1 if node i is a direct child of root
    model.z = pyo.Var(non_root, domain=pyo.Binary)

    # F[j] = subtree size rooted at j (counting j), for non-root nodes
    model.F = pyo.Var(non_root, domain=pyo.NonNegativeReals)

    # Each non-root node has exactly one incoming arc
    def in_arc_rule(m, j):
        return sum(m.x[i, j] for i in nodes if i != j) == 1
    model.in_arc = pyo.Constraint(non_root, rule=in_arc_rule)

    # Root has no incoming arc
    def root_no_in_rule(m):
        return sum(m.x[i, root] for i in nodes if i != root) == 0
    model.root_no_in = pyo.Constraint(rule=root_no_in_rule)

    # Root must have at least one outgoing arc
    def root_out_rule(m):
        return sum(m.x[root, j] for j in non_root) >= 1
    model.root_out = pyo.Constraint(rule=root_out_rule)

    # z[i] == x[root, i]
    def zdef_rule(m, i):
        return m.z[i] == m.x[root, i]
    model.zdef = pyo.Constraint(non_root, rule=zdef_rule)

    # Subtree size recurrence: F[j] = 1 + sum_{k != root, k != j} x[j,k] * F[k]
    # Also F[j] >= 1 (at least itself)
    def subtree_size_rule(m, j):
        return m.F[j] == 1 + sum(m.x[j, k] * m.F[k] for k in non_root if k != j)
    model.subtree_size = pyo.Constraint(non_root, rule=subtree_size_rule)

    # Port limit: if i is direct child of root, then F[i] <= port_limit
    def port_rule(m, i):
        return m.F[i] <= port_limit + bigM * (1 - m.z[i])
    model.port_rule = pyo.Constraint(non_root, rule=port_rule)

    # Objective: minimize cost of selected arcs
    def obj_rule(m):
        return sum(dist[(i, j)] * m.x[i, j] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}