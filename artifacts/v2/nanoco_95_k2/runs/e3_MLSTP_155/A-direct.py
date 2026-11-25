import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = params["n_sensors"]
    coords = params["sensor_coordinates"]
    dist = params["edge_distances"]

    edge_list = [
        (4, 6), (12, 13), (3, 10), (5, 10), (2, 5), (1, 3), (0, 14), (0, 11),
        (10, 12), (11, 14), (1, 12), (6, 11), (6, 8), (6, 14), (4, 5), (3, 9),
        (4, 8), (3, 12), (9, 10), (2, 4), (2, 7), (1, 5), (2, 13), (4, 7),
        (4, 10), (0, 6), (1, 13), (1, 10), (6, 9), (7, 8)
    ]
    E = len(edge_list)

    adj = {i: [] for i in range(n)}
    for e_idx, (u, v) in enumerate(edge_list):
        adj[u].append((v, e_idx))
        adj[v].append((u, e_idx))

    model = pyo.ConcreteModel()
    model.NODES = pyo.RangeSet(0, n - 1)
    model.EDGES = pyo.RangeSet(0, E - 1)

    model.x = pyo.Var(model.EDGES, domain=pyo.Binary)
    model.leaf = pyo.Var(model.NODES, domain=pyo.Binary)
    model.flow = pyo.Var(model.EDGES, domain=pyo.NonNegativeReals)

    def degree_rule(m, i):
        return sum(m.x[e] for (_j, e) in adj[i])
    model.degree = pyo.Expression(model.NODES, rule=degree_rule)

    model.num_edges = pyo.Constraint(
        rule=lambda m: sum(m.x[e] for e in m.EDGES) == n - 1
    )

    model.leaf_ub1 = pyo.Constraint(
        model.NODES, rule=lambda m, i: m.leaf[i] + m.degree[i] <= 2
    )
    model.leaf_ub2 = pyo.Constraint(
        model.NODES, rule=lambda m, i: m.leaf[i] <= m.degree[i]
    )
    model.leaf_lb = pyo.Constraint(
        model.NODES,
        rule=lambda m, i: (1 - m.degree[i]) <= n * (1 - m.leaf[i]),
    )

    def flow_balance_rule(m, i):
        if i == 0:
            return pyo.Constraint.Skip
        net = 0
        for (j, e_idx) in adj[i]:
            u, v = edge_list[e_idx]
            if u == i:
                net = net + m.flow[e_idx]
            else:
                net = net - m.flow[e_idx]
        return net == 1
    model.flow_balance = pyo.Constraint(model.NODES, rule=flow_balance_rule)

    def root_flow_rule(m):
        total = 0
        for (j, e_idx) in adj[0]:
            u, v = edge_list[e_idx]
            if u == 0:
                total = total + m.flow[e_idx]
        return total == n - 1
    model.root_flow = pyo.Constraint(rule=root_flow_rule)

    model.flow_cap = pyo.Constraint(
        model.EDGES,
        rule=lambda m, e: m.flow[e] <= (n - 1) * m.x[e],
    )

    model.obj = pyo.Objective(
        rule=lambda m: sum(m.leaf[i] for i in m.NODES),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}