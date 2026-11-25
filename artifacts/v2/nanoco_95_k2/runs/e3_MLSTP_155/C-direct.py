import gurobipy as gp
from gurobipy import GRB

def solve(params):
    sensor_coordinates = params["sensor_coordinates"]
    edge_distances = params["edge_distances"]
    n_sensors = params["n_sensors"]
    n_candidate_edges = params["n_candidate_edges"]

    candidate_edges = [
        (4, 6), (12, 13), (3, 10), (5, 10), (2, 5), (1, 3), (0, 14), (0, 11),
        (10, 12), (11, 14), (1, 12), (6, 11), (6, 8), (6, 14), (4, 5),
        (3, 9), (4, 8), (3, 12), (9, 10), (2, 4), (2, 7), (1, 5), (2, 13),
        (4, 7), (4, 10), (0, 6), (1, 13), (1, 10), (6, 9), (7, 8)
    ]

    n = n_sensors
    root = 0

    adj_out = {i: [] for i in range(n)}
    adj_in = {i: [] for i in range(n)}
    for e_idx, (u, v) in enumerate(candidate_edges):
        adj_out[u].append(e_idx)
        adj_in[v].append(e_idx)

    model = gp.Model("sensor_topology")
    model.Params.OutputFlag = 0

    x = model.addVars(n_candidate_edges, vtype=GRB.BINARY, name="x")
    y = model.addVars(n, vtype=GRB.BINARY, name="y")
    g = model.addVars(n_candidate_edges, lb=-(n - 1), ub=(n - 1), name="g")

    model.setObjective(gp.quicksum(y[i] for i in range(n)), GRB.MAXIMIZE)

    model.addConstr(gp.quicksum(x[e] for e in range(n_candidate_edges)) == n - 1)

    model.addConstr(
        gp.quicksum(g[e] for e in adj_out[root]) - gp.quicksum(g[e] for e in adj_in[root]) == n - 1,
        name="flow_root"
    )
    for i in range(n):
        if i == root:
            continue
        model.addConstr(
            gp.quicksum(g[e] for e in adj_out[i]) - gp.quicksum(g[e] for e in adj_in[i]) == -1,
            name=f"flow_{i}"
        )

    for e in range(n_candidate_edges):
        model.addConstr(g[e] <= (n - 1) * x[e])
        model.addConstr(g[e] >= -(n - 1) * x[e])

    for i in range(n):
        deg = gp.quicksum(x[e] for e in adj_out[i]) + gp.quicksum(x[e] for e in adj_in[i])
        model.addConstr(deg + (n - 1) * y[i] <= n)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "no_optimal"}