import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]

    num_peaks = 4
    num_aas = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables
    x = model.addVars(num_peaks, num_aas, vtype=GRB.BINARY, name="x")

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_peaks) for j in range(num_aas)),
        GRB.MINIMIZE
    )

    # Each peak assigned to at most one amino acid
    for i in range(num_peaks):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_aas)) <= 1, name=f"peak_{i}")

    # Each amino acid assigned to at most one peak
    for j in range(num_aas):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1, name=f"aa_{j}")

    # Exactly 3 assignments total
    model.addConstr(
        gp.quicksum(x[i, j] for i in range(num_peaks) for j in range(num_aas)) == 3,
        name="total_assignments"
    )

    # Pairwise restriction: if Peak 0 -> AA 1, then Peak 2 cannot -> AA 4
    model.addConstr(x[0, 1] + x[2, 4] <= 1, name="restrict_p0aa1_p2aa4")

    # Pairwise restriction: if Peak 1 -> AA 1, then Peak 2 cannot -> AA 4
    model.addConstr(x[1, 1] + x[2, 4] <= 1, name="restrict_p1aa1_p2aa4")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}