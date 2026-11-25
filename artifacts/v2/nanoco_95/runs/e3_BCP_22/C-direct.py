import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_nodes = int(params["num_nodes"])

    edges = [
        (0, 1, params["safety_buffer_0_1"]),
        (0, 7, params["safety_buffer_0_7"]),
        (1, 4, params["safety_buffer_1_4"]),
        (1, 7, params["safety_buffer_1_7"]),
        (4, 5, params["safety_buffer_4_5"]),
    ]

    # Upper bound on max slot: sum of all buffers is a safe ceiling
    slot_ub = int(sum(d for _, _, d in edges)) + num_nodes

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Gate slot variables: non-negative integers
    x = model.addVars(num_nodes, vtype=GRB.INTEGER, lb=0, ub=slot_ub, name="x")

    # Objective: minimize the maximum slot used
    z = model.addVar(vtype=GRB.INTEGER, lb=0, ub=slot_ub, name="z")
    model.setObjective(z, GRB.MINIMIZE)

    # z >= x_i for all i
    for i in range(num_nodes):
        model.addConstr(z >= x[i], name=f"max_slot_{i}")

    # Absolute difference constraints: |x_u - x_v| >= d
    # Linearized with a binary variable b_{u,v}: x_u - x_v >= d  OR  x_v - x_u >= d
    for idx, (u, v, d) in enumerate(edges):
        d_val = float(d)
        b = model.addVar(vtype=GRB.BINARY, name=f"b_{idx}")
        # b=0 => x_u - x_v >= d  (x_v <= x_u - d)
        # b=1 => x_v - x_u >= d  (x_u <= x_v - d)
        M = slot_ub + 1
        model.addConstr(x[u] - x[v] >= d_val - M * b,       name=f"sep_a_{idx}")
        model.addConstr(x[v] - x[u] >= d_val - M * (1 - b), name=f"sep_b_{idx}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}