import gurobipy as gp
from gurobipy import GRB


def solve(params):
    weight_0_3 = params["weight_0_3"]
    weight_1_5 = params["weight_1_5"]
    weight_2_4 = params["weight_2_4"]
    weight_3_4 = params["weight_3_4"]

    edges = [
        (0, 3, weight_0_3),
        (1, 5, weight_1_5),
        (2, 4, weight_2_4),
        (3, 4, weight_3_4),
    ]

    n_platforms = 6
    # Upper bound on any index: sum of all weights is a safe upper bound
    max_possible = int(sum(w for _, _, w in edges)) + n_platforms

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i] = platform index assigned to platform i (non-negative integer)
    x = model.addVars(n_platforms, vtype=GRB.INTEGER, lb=0, ub=max_possible, name="x")

    # z = maximum platform index used
    z = model.addVar(vtype=GRB.INTEGER, lb=0, ub=max_possible, name="z")

    # z >= x[i] for all i
    for i in range(n_platforms):
        model.addConstr(z >= x[i], name=f"max_bound_{i}")

    # Separation constraints: |x[u] - x[v]| >= d
    # Linearized with auxiliary binary b[e]: if b=1 then x[u]-x[v]>=d, else x[v]-x[u]>=d
    b = model.addVars(len(edges), vtype=GRB.BINARY, name="b")
    M = max_possible + 1  # big-M

    for idx, (u, v, d) in enumerate(edges):
        # x[u] - x[v] >= d - M*(1 - b[idx])
        model.addConstr(x[u] - x[v] >= d - M * (1 - b[idx]), name=f"sep_pos_{idx}")
        # x[v] - x[u] >= d - M*b[idx]
        model.addConstr(x[v] - x[u] >= d - M * b[idx], name=f"sep_neg_{idx}")

    model.setObjective(z, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}