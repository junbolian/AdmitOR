import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_peaks = 4
    num_aas = 5

    cost = {}
    for p in range(num_peaks):
        for a in range(num_aas):
            cost[p, a] = params[f"cost_peak{p}_aa{a}"]

    num_assignments = params["num_assignments"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_peaks, num_aas, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[p, a] * x[p, a] for p in range(num_peaks) for a in range(num_aas)),
        GRB.MINIMIZE
    )

    # Each peak assigned to at most one amino acid
    for p in range(num_peaks):
        model.addConstr(
            gp.quicksum(x[p, a] for a in range(num_aas)) <= 1,
            name=f"peak_{p}_atmost_one"
        )

    # Each amino acid assigned to at most one peak
    for a in range(num_aas):
        model.addConstr(
            gp.quicksum(x[p, a] for p in range(num_peaks)) <= 1,
            name=f"aa_{a}_atmost_one"
        )

    # Exactly num_assignments total assignments
    model.addConstr(
        gp.quicksum(x[p, a] for p in range(num_peaks) for a in range(num_aas)) == num_assignments,
        name="total_assignments"
    )

    # NOE constraints: the problem states that assigned amino acids for NOE-related peak
    # pairs must be within a distance threshold. No distance matrix or threshold value
    # is supplied in params, so the only constraint derivable from the problem structure
    # is that the two assigned amino acids must be distinct (they are already enforced
    # distinct by the amino acid uniqueness constraints above). No additional forbidden
    # pairs can be determined without explicit distance data, so no further NOE
    # constraints are added here.

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