import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    port_limit = params["port_limit"]
    cost = params["cost_matrix"]

    N = 16
    nodes = list(range(N))
    root = 0
    non_root = [i for i in nodes if i != root]

    # Directed arcs (child, parent): x[i,j] = 1 means parent of i is j
    arcs = [(i, j) for i in non_root for j in nodes if j != i]

    big_M = N

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.size = pyo.Var(nodes, domain=pyo.NonNegativeReals)
    model.flow = pyo.Var(arcs, domain=pyo.NonNegativeReals)

    def parent_rule(m, i):
        return sum(m.x[i, j] for j in nodes if j != i) == 1
    model.parent_con = pyo.Constraint(non_root, rule=parent_rule)

    # Root has no parent: outgoing arcs from root as child must be 0
    model.no_root_parent = pyo.Constraint(
        expr=sum(model.x[root, j] for j in nodes if j != root) == 0
    )

    def size_bigM_rule(m, i, j):
        return m.size[j] >= m.size[i] + 1 - big_M * (1 - m.x[i, j])
    model.size_link = pyo.Constraint(arcs, rule=size_bigM_rule)

    model.size_root = pyo.Constraint(expr=model.size[root] == N)
    model.size_lb = pyo.Constraint(nodes, rule=lambda m, i: m.size[i] >= 1)

    # Arcs into root (root's children): (i, root) for i in non_root
    root_children = [(i, root) for i in non_root]

    def port_rule(m, i, j):
        return m.size[i] <= port_limit + big_M * (1 - m.x[i, j])
    model.port_con = pyo.Constraint(root_children, rule=port_rule)

    def flow_cap_rule(m, i, j):
        return m.flow[i, j] <= big_M * m.x[i, j]
    model.flow_cap = pyo.Constraint(arcs, rule=flow_cap_rule)

    def out_expr(m, i):
        return sum(m.flow[i, j] for j in nodes if j != i)

    def in_expr(m, i):
        return sum(m.flow[j, i] for j in nodes if j != i)

    def flow_balance_root(m):
        return out_expr(m, root) - in_expr(m, root) == (N - 1)
    model.flow_root = pyo.Constraint(rule=flow_balance_root)

    def flow_balance_nonroot(m, i):
        return in_expr(m, i) - out_expr(m, i) == 1
    model.flow_nonroot = pyo.Constraint(non_root, rule=flow_balance_nonroot)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for (i, j) in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}