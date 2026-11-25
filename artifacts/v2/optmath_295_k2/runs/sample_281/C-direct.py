import gurobipy as gp
from gurobipy import GRB

def solve(params):
    assignment_costs = params["assignment_costs"]
    total_assignments_required = params["total_assignments_required"]

    num_peaks = 5
    num_amino_acids = 6

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables x[i, j]: 1 if peak i is assigned to amino acid j
    x = model.addVars(num_peaks, num_amino_acids, vtype=GRB.BINARY, name="x")

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(assignment_costs[i][j] * x[i, j]
                    for i in range(num_peaks)
                    for j in range(num_amino_acids)),
        GRB.MINIMIZE
    )

    # Each peak assigned to at most one amino acid
    for i in range(num_peaks):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_amino_acids)) <= 1,
            name=f"peak_{i}_once"
        )

    # Each amino acid assigned to at most one peak
    for j in range(num_amino_acids):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1,
            name=f"aa_{j}_once"
        )

    # Exactly total_assignments_required assignments
    model.addConstr(
        gp.quicksum(x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)) == total_assignments_required,
        name="total_assignments"
    )

    # NOE constraints derived from the problem description
    # If Peak 0 -> AA 0, then Peak 4 cannot be assigned to AA 1, 3, or 4
    model.addConstr(x[0, 0] + x[4, 1] <= 1, name="NOE_0_4_0_1")
    model.addConstr(x[0, 0] + x[4, 3] <= 1, name="NOE_0_4_0_3")
    model.addConstr(x[0, 0] + x[4, 4] <= 1, name="NOE_0_4_0_4")

    # If Peak 1 -> AA 0, then Peak 2 cannot be assigned to AA 1, 3, or 4
    model.addConstr(x[1, 0] + x[2, 1] <= 1, name="NOE_1_2_0_1")
    model.addConstr(x[1, 0] + x[2, 3] <= 1, name="NOE_1_2_0_3")
    model.addConstr(x[1, 0] + x[2, 4] <= 1, name="NOE_1_2_0_4")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}