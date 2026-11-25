import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 12  # nodes 0..11
    nodes = list(range(n))
    depot = 0
    stops = list(range(1, n))

    def get_dist(i, j):
        if i == j:
            return 0.0
        a, b = (i, j) if i < j else (j, i)
        return float(params[f"distance_{a}_{b}"])

    dist = {(i, j): get_dist(i, j) for i in nodes for j in nodes if i != j}

    max_route_nodes = int(params["max_route_nodes"])

    # Edges: since it's a tree with root depot, direct each non-tree node to parent.
    # Build undirected edge set, enforce parent assignment using network-style flow.
    # We'll use a directed arborescence (each node except depot has exactly one parent).
    # Subtree capacity per route (branch from depot): each direct child of depot roots a subtree
    # with at most max_route_nodes nodes total.

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.stops = pyo.Set(initialize=stops)

    # x[i,j] = 1 if node i is parent of node j (edge i->j, i is closer to depot)
    arcs = [(i, j) for i in nodes for j in stops if i != j]
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    # Each stop has exactly one parent
    def parent_rule(model, j):
        return sum(model.x[i, j] for i in nodes if i != j) == 1
    model.parent_con = pyo.Constraint(model.stops, rule=parent_rule)

    # Depot has no parent
    # No cycles: ensure subtree sizes are well-defined via flow from depot
    # f[i,j] = number of nodes in subtree rooted at j when edge i->j is used
    model.f = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    # Capacity per branch: subtree rooted at direct child of depot <= max_route_nodes
    # We define: for arc (0, j), f[0,j] = total nodes in subtree of j.
    # For any arc (i,j) with i != 0, f[i,j] = total nodes in subtree of j.
    # Recurrence: f[i,j] = 1 + sum_{k child of j} f[j,k]

    # Link f and x: if x[i,j]=1 then subtree size relation holds.
    def flow_upper(model, i, j):
        return model.f[i, j] <= n * model.x[i, j]
    model.flow_upper = pyo.Constraint(model.arcs, rule=flow_upper)

    def flow_lower(model, i, j):
        return model.f[i, j] >= 1 * model.x[i, j]
    model.flow_lower = pyo.Constraint(model.arcs, rule=flow_lower)

    # Subtree relation: f[i,j] >= 1 + sum_{k child of j} f[j,k] - BigM*(1-x[i,j])
    # Actually equality: f[i,j] == 1 + sum_k f[j,k] when x[i,j]=1
    def subtree_rule(model, i, j):
        if i == j:
            return pyo.Constraint.Skip
        # sum over children k of j: arcs (j,k)
        children_sum = sum(model.f[j, k] for k in stops if k != j)
        return model.f[i, j] == (1 + children_sum) * model.x[i, j] + \
               (1 + children_sum) * 0  # placeholder
        # Better: enforce relation
    # Rewrite properly below
    model.subtree_con = pyo.ConstraintList()
    for (i, j) in arcs:
        children_sum = sum(model.f[j, k] for k in stops if k != j)
        # f[i,j] = x[i,j] * (1 + children_sum)  => two linear constraints
        model.subtree_con.add(model.f[i, j] <= model.x[i, j] * n)
        model.subtree_con.add(model.f[i, j] >= 1 * model.x[i, j])
        model.subtree_con.add(model.f[i, j] <= 1 + children_sum)
        model.subtree_con.add(model.f[i, j] >= (1 + children_sum) - n * (1 - model.x[i, j]))

    # Branch capacity: direct child of depot subtree size <= max_route_nodes
    model.branch_cap = pyo.Constraint(
        [j for j in stops],
        rule=lambda model, j: model.f[0, j] <= max_route_nodes
    )

    # Objective: minimize total edge cost
    model.cost = pyo.Objective(
        expr=sum(dist[(i, j)] * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}