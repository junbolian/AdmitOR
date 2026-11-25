import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    available_edges = params["available_edges"]
    num_nodes = 12
    nodes = list(range(num_nodes))

    # Remove self-loops / normalize, keep fixed structure only
    edges = []
    for u, v in available_edges:
        if u != v:
            edges.append((u, v))
    E = list(range(len(edges)))

    # Undirected incidence lookup
    incident = {i: [] for i in nodes}
    for k in E:
        u, v = edges[k]
        incident[u].append(k)
        incident[v].append(k)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(E, domain=pyo.Binary)
    # leaf[i] = 1 if node i has degree exactly one
    model.leaf = pyo.Var(nodes, domain=pyo.Binary)

    def degree_rule(m, i):
        return sum(m.x[k] for k in incident[i])

    # Every node must have degree >= 1 (linked into network)
    model.degree_ge = pyo.Constraint(nodes, rule=lambda m, i: sum(m.x[k] for k in incident[i]) >= 1)
    # Every node degree <= 2 is NOT required generally; but for leaf = exactly degree 1 we
    # need leaf <= degree and degree - leaf bounds. With tree of 12 nodes, max degree <= 11.
    # leaf[i] <= degree[i]
    model.leaf_le = pyo.Constraint(nodes, rule=lambda m, i: m.leaf[i] <= sum(m.x[k] for k in incident[i]))
    # degree[i] - leaf[i] <= (num_nodes - 2) * (1 - leaf[i])  => if leaf=1, degree>=1; if leaf=0, degree>=2? 
    # We want leaf=1 iff degree==1. Enforce: degree - 1 <= M*(1-leaf) and leaf>=1-... 
    # Simpler: leaf <= degree ; and degree - 1 <= (num_nodes-2)*(1 - leaf)
    # If leaf=1: degree - 1 <= 0 => degree <= 1, combined leaf<=degree gives degree=1.
    # If leaf=0: degree - 1 <= num_nodes-2 => always true, leaf can be 0 even if degree=1? Then leaf=0 allowed when degree=1. Not exact.
    # Fix: force leaf = degree==1 exactly via: leaf >= degree - 1 ... but degree can be 0? we enforce >=1.
    # Use: degree - 1 >= (leaf - 1)*M  ... alternative: leaf >= 1 - (degree-1) not linear-friendly with binary.
    # Standard trick: leaf=1 => degree==1 ; degree==1 => leaf=1.
    # degree - 1 <= (num_nodes-2)*(1-leaf)
    # and leaf <= degree  (leaf=1=>degree>=1), and add degree <= 1 + (num_nodes-1)*(1-leaf) subsumed by first since num_nodes-2.
    Mbig = num_nodes  # safe upper bound on degree
    model.leaf_upper = pyo.Constraint(nodes, rule=lambda m, i: sum(m.x[k] for k in incident[i]) - 1 <= (Mbig - 2) * (1 - m.leaf[i]))
    # Now ensure degree==1 => leaf=1: if leaf=0 then degree-1 <= Mbig-2 (weak). Need reverse.
    # Add: 1 - leaf[i] <= (sum x - 1) ... i.e. leaf>=1 when degree>=1? No.
    # Force: if degree==1 then leaf=1: degree>=2 OR leaf=1 => (1-leaf)*? use: leaf[i] >= 1 - (sum x - 1) is nonlinear.
    # Linear form: sum x - 1 <= (Mbig-1)*(1-leaf) already covers leaf=1=>deg<=1. For deg=1=>leaf=1:
    # leaf[i] >= sum x - 1  is not enough (deg=1 => leaf>=0 only).
    # Use: leaf[i] >= (sum x - 1) / (Mbig-1) not integer.
    # Stronger: deg == 1 iff leaf==1. Encode: deg - 1 <= (Mbig-2)*(1-leaf) AND 1 - leaf <= deg - 1? 
    # 1 - leaf <= deg - 1  => leaf >= 2 - deg. If deg=1 => leaf>=1 => leaf=1. If deg=2 => leaf>=0. Good!
    model.leaf_lower = pyo.Constraint(nodes, rule=lambda m, i: 1 - m.leaf[i] <= sum(m.x[k] for k in incident[i]) - 1)

    # Spanning tree: exactly num_nodes-1 edges
    model.edge_count = pyo.Constraint(expr=sum(model.x[k] for k in E) == num_nodes - 1)

    # Connectedness: single-commodity flow from root node 0
    root = 0
    # flow f[k,i] on edge k in direction toward i? Use directed flows on undirected edges.
    # Create directed arcs (2 per edge)
    arcs = []
    for k in E:
        u, v = edges[k]
        arcs.append((k, u, v))
        arcs.append((k, v, u))
    A = list(range(len(arcs)))

    model.f = pyo.Var(A, domain=pyo.NonNegativeReals)
    # capacity: f on arc <= (num_nodes-1)*x[k]
    model.flow_cap = pyo.Constraint(
        A, rule=lambda m, a: m.f[a] <= (num_nodes - 1) * m.x[arcs[a][0]]
    )

    # Flow conservation: root sends num_nodes-1 units
    out_arcs = {i: [] for i in nodes}
    in_arcs = {i: [] for i in nodes}
    for a, (k, u, v) in enumerate(arcs):
        out_arcs[u].append(a)
        in_arcs[v].append(a)

    def flow_bal(m, i):
        out_v = sum(m.f[a] for a in out_arcs[i])
        in_v = sum(m.f[a] for a in in_arcs[i])
        if i == root:
            return out_v - in_v == num_nodes - 1
        else:
            return in_v - out_v == 1
    model.flow_bal = pyo.Constraint(nodes, rule=flow_bal)

    model.obj = pyo.Objective(expr=sum(model.leaf[i] for i in nodes), sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}