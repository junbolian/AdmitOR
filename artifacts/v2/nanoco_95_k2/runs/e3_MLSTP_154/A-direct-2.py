import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance = params["distance_matrix"]
    approved = params["approved_edges"]

    n = len(distance)

    # Canonical undirected edge list
    edge_list = []
    seen = set()
    for u, v in approved:
        key = (min(u, v), max(u, v))
        if key not in seen:
            seen.add(key)
            edge_list.append(key)
    m = len(edge_list)

    model = pyo.ConcreteModel()
    model.V = pyo.RangeSet(0, n - 1)
    model.E = pyo.RangeSet(0, m - 1)

    model.x = pyo.Var(model.E, domain=pyo.Binary)

    inc = {v: [] for v in range(n)}
    for i, (u, w) in enumerate(edge_list):
        inc[u].append(i)
        inc[w].append(i)

    # Degree of each node (integer since x binary)
    model.deg = pyo.Var(model.V, domain=pyo.NonNegativeIntegers)
    model.deg_con = pyo.Constraint(
        model.V,
        rule=lambda mdl, v: mdl.deg[v] == sum(mdl.x[i] for i in inc[v]),
    )

    # Leaf indicator: leaf[v] == 1 iff deg[v] == 1
    # leaf[v] <= deg[v]
    # leaf[v] <= 2 - deg[v]
    model.leaf = pyo.Var(model.V, domain=pyo.Binary)
    model.leaf_ub = pyo.Constraint(
        model.V, rule=lambda mdl, v: mdl.leaf[v] <= mdl.deg[v]
    )
    model.leaf_lb = pyo.Constraint(
        model.V, rule=lambda mdl, v: mdl.leaf[v] <= 2 - mdl.deg[v]
    )

    # Spanning tree: exactly n-1 edges
    model.n_edges = pyo.Constraint(
        expr=sum(model.x[i] for i in model.E) == n - 1
    )

    # Single-commodity flow rooted at node 0 for connectivity.
    # Use separate directed flow variables per edge to avoid bilinear products.
    # f_low2high[i]: flow from low endpoint to high endpoint
    # f_high2low[i]: flow from high endpoint to low endpoint
    model.f_lh = pyo.Var(model.E, domain=pyo.NonNegativeReals, bounds=(0, n - 1))
    model.f_hl = pyo.Var(model.E, domain=pyo.NonNegativeReals, bounds=(0, n - 1))

    # Flow only on selected edges
    model.flow_link_lh = pyo.Constraint(
        model.E, rule=lambda mdl, i: mdl.f_lh[i] <= (n - 1) * mdl.x[i]
    )
    model.flow_link_hl = pyo.Constraint(
        model.E, rule=lambda mdl, i: mdl.f_hl[i] <= (n - 1) * mdl.x[i]
    )

    def flow_balance(mdl, v):
        net_out = 0.0
        for i in inc[v]:
            u, w = edge_list[i]
            if v == u:
                net_out = net_out + mdl.f_lh[i] - mdl.f_hl[i]
            else:
                net_out = net_out + mdl.f_hl[i] - mdl.f_lh[i]
        if v == 0:
            return net_out == n - 1
        else:
            return net_out == -1

    model.flow_balance = pyo.Constraint(model.V, rule=flow_balance)

    model.obj = pyo.Objective(
        expr=sum(model.leaf[v] for v in model.V), sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}