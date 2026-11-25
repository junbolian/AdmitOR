import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    num_assignments = params["num_assignments"]
    peak_capacity = params["peak_capacity"]
    amino_acid_capacity = params["amino_acid_capacity"]

    num_peaks = len(cost)
    num_amino_acids = len(cost[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = 1 if peak i assigned to amino acid j
    x = model.addVars(num_peaks, num_amino_acids, vtype=GRB.BINARY, name="x")

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)),
        GRB.MINIMIZE
    )

    # Each peak assigned to at most peak_capacity amino acids
    for i in range(num_peaks):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_amino_acids)) <= peak_capacity,
            name=f"peak_cap_{i}"
        )

    # Each amino acid assigned to at most amino_acid_capacity peaks
    for j in range(num_amino_acids):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_peaks)) <= amino_acid_capacity,
            name=f"aa_cap_{j}"
        )

    # Exactly num_assignments total assignments
    model.addConstr(
        gp.quicksum(x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)) == num_assignments,
        name="total_assignments"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}