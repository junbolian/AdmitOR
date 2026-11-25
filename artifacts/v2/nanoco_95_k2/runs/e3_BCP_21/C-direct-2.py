import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edge_weights = params["edge_weights"]

    edges = [
        (0, 1), (0, 2), (1, 3), (1, 4), (1, 5),
        (2, 7), (3, 4), (3, 5), (4, 5), (4, 6), (4, 7), (5, 6)
    ]

    if len(edge_weights) != len(edges):
        return {"objective": None, "status": "invalid params"}

    n_nets = 8
    # Upper bound on any track assignment: sum of all weights is a safe upper bound
    big_m = sum(edge_weights)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Track assignment variables for each net
    track = model.addVars(n_nets, vtype=GRB.INTEGER, lb=0, ub=big_m, name="track")

    # Minimax variable: the maximum track assignment
    max_track = model.addVar(vtype=GRB.INTEGER, lb=0, ub=big_m, name="max_track")

    # Objective: minimize the maximum track assignment
    model.setObjective(max_track, GRB.MINIMIZE)

    # max_track >= track[i] for all i
    for i in range(n_nets):
        model.addConstr(max_track >= track[i], name=f"max_bound_{i}")

    # For each edge (u, v) with weight d: |track[u] - track[v]| >= d
    # Linearize: introduce binary b_{e} in {0,1} such that
    #   track[u] - track[v] >= d  if b=1
    #   track[v] - track[u] >= d  if b=0
    b = model.addVars(len(edges), vtype=GRB.BINARY, name="b")

    for idx, ((u, v), d) in enumerate(zip(edges, edge_weights)):
        # track[u] - track[v] >= d - big_m*(1 - b[idx])
        model.addConstr(
            track[u] - track[v] >= d - big_m * (1 - b[idx]),
            name=f"sep_pos_{idx}"
        )
        # track[v] - track[u] >= d - big_m * b[idx]
        model.addConstr(
            track[v] - track[u] >= d - big_m * b[idx],
            name=f"sep_neg_{idx}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(max_track.X), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}