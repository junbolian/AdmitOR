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

    # Upper bound on gate slots: sum of all safety buffers is a safe upper bound
    big_m = int(sum(d for _, _, d in edges)) + num_nodes

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Gate slot variables for each aircraft
    x = model.addVars(num_nodes, lb=0, ub=big_m, vtype=GRB.INTEGER, name="x")

    # Objective: minimize the maximum gate slot used
    z = model.addVar(lb=0, ub=big_m, vtype=GRB.INTEGER, name="z")
    model.setObjective(z, GRB.MINIMIZE)

    # z >= x_i for all i
    for i in range(num_nodes):
        model.addConstr(z >= x[i], name=f"max_gate_{i}")

    # Separation constraints: |x_u - x_v| >= d
    # Linearized with binary indicator b[e] where b=1 means x_u - x_v >= d, b=0 means x_v - x_u >= d
    b = model.addVars(len(edges), vtype=GRB.BINARY, name="b")

    for idx, (u, v, d) in enumerate(edges):
        # Either x_u - x_v >= d  OR  x_v - x_u >= d
        # b[idx] = 1 => x_u - x_v >= d
        # b[idx] = 0 => x_v - x_u >= d
        model.addConstr(
            x[u] - x[v] >= d - big_m * (1 - b[idx]),
            name=f"sep_pos_{idx}"
        )
        model.addConstr(
            x[v] - x[u] >= d - big_m * b[idx],
            name=f"sep_neg_{idx}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}