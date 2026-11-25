import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    exact_assignments = params["exact_assignments"]
    
    # Try multiple possible key names for NOE parameters
    noe_key = None
    for candidate in ["noe_parameters", "noe_params", "noe", "NOE_parameters", "noe_matrix"]:
        if candidate in params:
            noe_key = candidate
            break
    
    if noe_key is None:
        # Try to find any key that contains 'noe' (case-insensitive)
        for k in params:
            if 'noe' in k.lower():
                noe_key = k
                break
    
    if noe_key is None:
        return {"objective": None, "status": "missing noe parameter"}
    
    noe_parameters = params[noe_key]

    num_peaks = len(cost_matrix)        # 5
    num_aas = len(cost_matrix[0])       # 6

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables: x[i,j] = 1 if Peak i assigned to AA j
    x = model.addVars(num_peaks, num_aas, vtype=GRB.BINARY, name="x")

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j]
                    for i in range(num_peaks)
                    for j in range(num_aas)),
        GRB.MINIMIZE
    )

    # Each peak assigned to at most one amino acid
    for i in range(num_peaks):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_aas)) <= 1,
            name=f"peak_{i}_atmost1"
        )

    # Each amino acid receives at most one peak
    for j in range(num_aas):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1,
            name=f"aa_{j}_atmost1"
        )

    # Exactly `exact_assignments` total assignments
    model.addConstr(
        gp.quicksum(x[i, j] for i in range(num_peaks) for j in range(num_aas)) == exact_assignments,
        name="exact_assignments"
    )

    # NOE constraints:
    # noe_parameters[a][b] == 1 means AA a and AA b are spatially proximate.
    # For all peak pairs (i, k) with i != k, and AA pairs (a, b) where
    # noe_parameters[a][b] == 1: x[i,a] + x[k,b] <= 1.
    num_aa_noe = len(noe_parameters)
    for a in range(num_aa_noe):
        for b in range(len(noe_parameters[a])):
            if noe_parameters[a][b] == 1:
                for i in range(num_peaks):
                    for k in range(num_peaks):
                        if i != k:
                            model.addConstr(
                                x[i, a] + x[k, b] <= 1,
                                name=f"noe_p{i}_aa{a}_p{k}_aa{b}"
                            )

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