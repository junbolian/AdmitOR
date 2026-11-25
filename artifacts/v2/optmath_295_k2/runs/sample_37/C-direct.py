import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]

    num_peaks = 4
    num_amino_acids = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if peak i assigned to amino acid j
    x = model.addVars(num_peaks, num_amino_acids, vtype=GRB.BINARY, name="x")

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)),
        GRB.MINIMIZE
    )

    # Each peak assigned to at most one amino acid
    for i in range(num_peaks):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_amino_acids)) <= 1, name=f"peak_{i}")

    # Each amino acid assigned to at most one peak
    for j in range(num_amino_acids):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1, name=f"amino_{j}")

    # Exactly 3 assignments total
    model.addConstr(
        gp.quicksum(x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)) == 3,
        name="total_assignments"
    )

    # Distance-based pair restrictions:
    # If Peak 0 assigned to Amino Acid 1, then Peak 2 cannot be assigned to Amino Acid 4
    model.addConstr(x[0, 1] + x[2, 4] <= 1, name="pair_restrict_0")

    # If Peak 1 assigned to Amino Acid 1, then Peak 2 cannot be assigned to Amino Acid 4
    model.addConstr(x[1, 1] + x[2, 4] <= 1, name="pair_restrict_1")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}