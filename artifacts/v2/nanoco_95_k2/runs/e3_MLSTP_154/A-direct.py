import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    approved_edges = params["approved_edges"]

    n = len(distance_matrix)

    # Normalize edges to tuples of ints
    edges = [(int(u), int(v)) for (u, v) in approved_edges]

    model = pyo.ConcreteModel()

    # Edge selection variables (1 if edge chosen in the spanning tree)
    model.x = pyo.Var(range(len(edges)), domain=pyo.Binary)

    # Model as a maximum spanning tree subject to connectivity using flow constraints.
    # Objective component stored for retrieval.
    def obj_rule(md):
        return sum(md.x[i] for i in range(len(edges)))

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Spanning tree: exactly n-1 edges selected
    def tree_size_rule(md):
        return sum(md.x[i] for i in range(len(edges))) == n - 1

    model.tree_size = pyo.Constraint(rule=tree_size_rule)

    # Connectivity via single-commodity flow rooted at node 0.
    # Each non-root node must have net inflow of 1.
    # Directed arcs: allow flow in both directions along each approved edge.
    # If edge not selected, no flow allowed on either direction.
    root = 0

    # Flow variables indexed by (edge_index, direction)
    arcs = []
    for i in range(len(edges)):
        u, v = edges[i]
        arcs.append((i, u, v, 0))  # direction 0: u -> v
        arcs.append((i, u, v, 1))  # direction 1: v -> u
    arc_index = list(range(len(arcs)))

    model.flow = pyo.Var(arc_index, domain=pyo.NonNegativeReals)

    # Capacity constraints: flow <= (n-1) * x on each directed arc
    def cap_rule(md, a):
        i, u, v, d = arcs[a]
        return md.flow[a] <= (n - 1) * md.x[i]

    model.cap = pyo.Constraint(arc_index, rule=cap_rule)

    # Build incidence (net outflow minus inflow) per node
    # For each node, sum of outgoing flow - sum of incoming flow = supply
    # supply = n-1 for root, -1 for every other node.
    node_arcs_out = {j: [] for j in range(n)}
    node_arcs_in = {j: [] for j in range(n)}

    for a in arc_index:
        i, u, v, d = arcs[a]
        if d == 0:
            src, dst = u, v
        else:
            src, dst = v, u
        node_arcs_out[src].append(a)
        node_arcs_in[dst].append(a)

    def balance_rule(md, j):
        out_flow = sum(md.flow[a] for a in node_arcs_out[j])
        in_flow = sum(md.flow[a] for a in node_arcs_in[j])
        if j == root:
            return out_flow - in_flow == n - 1
        else:
            return out_flow - in_flow == -1

    model.balance = pyo.Constraint(range(n), rule=balance_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}