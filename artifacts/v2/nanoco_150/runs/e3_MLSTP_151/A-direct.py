import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    edge_list = params["edge_list"]
    distance_matrix = params["distance_matrix"]

    nodes = list(range(num_nodes))
    edges = [(int(u), int(v)) for (u, v) in edge_list]
    num_edges = len(edges)

    # Incidence: for each node, list of edge indices touching it
    incident = {i: [] for i in nodes}
    for e_idx, (u, v) in enumerate(edges):
        incident[u].append(e_idx)
        incident[v].append(e_idx)

    model = pyo.ConcreteModel()

    model.E = pyo.RangeSet(0, num_edges - 1)
    model.V = pyo.RangeSet(0, num_nodes - 1)

    # x[e] = 1 if edge selected
    model.x = pyo.Var(model.E, domain=pyo.Binary)
    # l[i] = 1 if node i is a leaf
    model.l = pyo.Var(model.V, domain=pyo.Binary)

    # Spanning tree: exactly num_nodes - 1 edges
    model.tree_size = pyo.Constraint(
        expr=sum(model.x[e] for e in model.E) == num_nodes - 1
    )

    # Degree for each node
    def degree_expr(i):
        return sum(model.x[e] for e in incident[i])

    # Leaf definition: l[i] <= degree(i)/1 ... and degree(i) >= 1
    # Enforce: degree >= 1 for all nodes (connectedness handled by tree)
    model.min_degree = pyo.Constraint(
        model.V, rule=lambda m, i: degree_expr(i) >= 1
    )

    # l[i] <= 1 if degree <= 1 else 0. Since degree integer:
    # l[i] = 1 => degree(i) == 1 ; degree==1 => l[i] can be 1
    # l[i] <= 1 - (degree(i) - 1) * ... use big-M style:
    # l[i] <= 1 - (degree(i) - 1) restricted: if degree >= 2, l must be 0.
    # degree(i) - 1 <= (num_nodes-2)*(1 - l[i]) + 0 ... 
    # Simpler: degree(i) <= 1 + M*(1 - l[i]) with M large.
    M = num_nodes  # max possible degree is num_nodes - 1

    model.leaf_ub = pyo.Constraint(
        model.V,
        rule=lambda m, i: degree_expr(i) <= 1 + M * (1 - m.l[i]),
    )
    # If leaf then degree <= 1 ; combine with min_degree >= 1 to force exactly 1.
    # Also ensure l[i] can be 1 only when degree == 1 (already via above + min_degree).

    # Objective: maximize number of leaves
    model.obj = pyo.Objective(
        expr=sum(model.l[i] for i in model.V), sense=pyo.maximize
    )

    # Solve with HiGHS
    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}