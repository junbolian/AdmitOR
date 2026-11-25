import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    exact_assignments = params["exact_assignments"]

    # Try multiple possible key names for NOE parameters
    if "noe_parameters" in params:
        noe_parameters = params["noe_parameters"]
    elif "noe_params" in params:
        noe_parameters = params["noe_params"]
    elif "noe" in params:
        noe_parameters = params["noe"]
    else:
        # No NOE constraints provided; default to all zeros
        num_aa_fallback = len(cost_matrix[0])
        noe_parameters = [[0] * num_aa_fallback for _ in range(num_aa_fallback)]

    num_peaks = len(cost_matrix)
    num_aas = len(cost_matrix[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables: x[i,j] = 1 if peak i assigned to AA j
    x = {}
    for i in range(num_peaks):
        for j in range(num_aas):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in range(num_peaks) for j in range(num_aas)),
        GRB.MINIMIZE
    )

    # Each peak assigned to at most one AA
    for i in range(num_peaks):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_aas)) <= 1, name=f"peak_{i}")

    # Each AA receives at most one peak
    for j in range(num_aas):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1, name=f"aa_{j}")

    # Exactly `exact_assignments` total assignments
    model.addConstr(
        gp.quicksum(x[i, j] for i in range(num_peaks) for j in range(num_aas)) == exact_assignments,
        name="exact_assign"
    )

    # NOE constraints: if noe_parameters[a1][a2] == 1, for any peak p1 assigned to a1
    # and any peak p2 assigned to a2 (p1 != p2), they cannot both be assigned.
    # x[p1, a1] + x[p2, a2] <= 1 for all p1 != p2
    for a1 in range(len(noe_parameters)):
        for a2 in range(len(noe_parameters[a1])):
            if a1 != a2 and noe_parameters[a1][a2] == 1:
                for p1 in range(num_peaks):
                    for p2 in range(num_peaks):
                        if p1 != p2:
                            model.addConstr(
                                x[p1, a1] + x[p2, a2] <= 1,
                                name=f"noe_{p1}_{a1}_{p2}_{a2}"
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