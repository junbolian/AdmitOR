import gurobipy as gp
from gurobipy import GRB

def solve(params):
    safety_buffer_0_1 = params["safety_buffer_0_1"]
    safety_buffer_0_7 = params["safety_buffer_0_7"]
    safety_buffer_1_4 = params["safety_buffer_1_4"]
    safety_buffer_1_7 = params["safety_buffer_1_7"]
    safety_buffer_4_5 = params["safety_buffer_4_5"]
    num_nodes = params["num_nodes"]

    edges = [
        (0, 1, safety_buffer_0_1),
        (0, 7, safety_buffer_0_7),
        (1, 4, safety_buffer_1_4),
        (1, 7, safety_buffer_1_7),
        (4, 5, safety_buffer_4_5),
    ]

    # Upper bound on any slot: sum of all buffers is a safe upper bound
    slot_ub = int(sum(d for _, _, d in edges)) + num_nodes

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i]: gate slot assigned to aircraft i
    x = model.addVars(num_nodes, vtype=GRB.INTEGER, lb=0, ub=slot_ub, name="x")

    # z: maximum slot used
    z = model.addVar(vtype=GRB.INTEGER, lb=0, ub=slot_ub, name="z")

    model.setObjective(z, GRB.MINIMIZE)

    # z >= x[i] for all i
    for i in range(num_nodes):
        model.addConstr(z >= x[i], name=f"z_bound_{i}")

    # Absolute difference constraints via big-M linearization
    # For each edge (u, v, d): |x[u] - x[v]| >= d
    # Introduce binary b[e]: if b[e]=1 then x[u]-x[v] >= d, else x[v]-x[u] >= d
    M = slot_ub + 1

    for idx, (u, v, d) in enumerate(edges):
        b = model.addVar(vtype=GRB.BINARY, name=f"b_{idx}")
        # b=1: x[u] - x[v] >= d  =>  x[v] - x[u] <= -d  (enforced when b=1)
        # b=0: x[v] - x[u] >= d  (enforced when b=0)
        # Using big-M:
        # x[u] - x[v] >= d - M*(1 - b)
        # x[v] - x[u] >= d - M*b
        model.addConstr(x[u] - x[v] >= d - M * (1 - b), name=f"sep_ab_{idx}")
        model.addConstr(x[v] - x[u] >= d - M * b, name=f"sep_ba_{idx}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}