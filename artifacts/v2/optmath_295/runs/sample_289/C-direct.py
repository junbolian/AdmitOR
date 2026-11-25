import gurobipy as gp
from gurobipy import GRB


def solve(params):
    assignment_cost = params["assignment_cost"]
    num_assignments_required = params["num_assignments_required"]
    num_peaks = params["num_peaks"]
    num_amino_acids = params["num_amino_acids"]

    model = gp.Model("nmr_peak_assignment")
    model.Params.OutputFlag = 0

    # Decision variables: x[i, j] = 1 if peak i is assigned to amino acid j
    x = {}
    for i in range(num_peaks):
        for j in range(num_amino_acids):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(
            assignment_cost[i][j] * x[i, j]
            for i in range(num_peaks)
            for j in range(num_amino_acids)
        ),
        GRB.MINIMIZE,
    )

    # Each amino acid assigned to at most one peak
    for j in range(num_amino_acids):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1)

    # Each peak assigned to at most one amino acid
    for i in range(num_peaks):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_amino_acids)) <= 1)

    # Exactly the required number of assignments
    model.addConstr(
        gp.quicksum(
            x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)
        )
        == num_assignments_required
    )

    # NOE constraints (24 total).
    # For every ordered peak pair (i, k) with i < k (6 pairs),
    # if peak i is assigned to amino acid in {0, 1}, then peak k
    # cannot be assigned to amino acid in {3, 4}.
    # 6 peak pairs * 2 source amino acids * 2 target amino acids = 24.
    # This matches the stated examples for the (Peak 0, Peak 3) pair:
    #   x[0,0]+x[3,3]<=1, x[0,0]+x[3,4]<=1,
    #   x[0,1]+x[3,3]<=1, x[0,1]+x[3,4]<=1.
    noe_source_aas = (0, 1)
    noe_target_aas = (3, 4)
    for i in range(num_peaks):
        for k in range(i + 1, num_peaks):
            for s_aa in noe_source_aas:
                if s_aa >= num_amino_acids:
                    continue
                for t_aa in noe_target_aas:
                    if t_aa >= num_amino_acids:
                        continue
                    model.addConstr(x[i, s_aa] + x[k, t_aa] <= 1)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}