import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    n_assignments = params["n_assignments"]

    n_peaks = 4
    n_amino = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if peak i assigned to amino acid j
    x = model.addVars(n_peaks, n_amino, vtype=GRB.BINARY, name="x")

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in range(n_peaks) for j in range(n_amino)),
        GRB.MINIMIZE
    )

    # Each peak assigned to at most one amino acid
    for i in range(n_peaks):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n_amino)) <= 1, name=f"peak_{i}")

    # Each amino acid assigned to at most one peak
    for j in range(n_amino):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n_peaks)) <= 1, name=f"amino_{j}")

    # Exactly n_assignments assignments total
    model.addConstr(
        gp.quicksum(x[i, j] for i in range(n_peaks) for j in range(n_amino)) == n_assignments,
        name="total_assignments"
    )

    # Pairwise distance constraints:
    # If Peak 0 assigned to Amino Acid 1, Peak 2 cannot be assigned to Amino Acid 4
    model.addConstr(x[0, 1] + x[2, 4] <= 1, name="dist_0_1_2_4")
    # If Peak 1 assigned to Amino Acid 1, Peak 2 cannot be assigned to Amino Acid 4
    model.addConstr(x[1, 1] + x[2, 4] <= 1, name="dist_1_1_2_4")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}