import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_peaks = 4
    num_aas = 5

    # Build cost matrix from params
    cost = {}
    for p in range(num_peaks):
        for a in range(num_aas):
            key = f"cost_peak{p}_aa{a}"
            cost[(p, a)] = params[key]

    num_assignments_required = params["num_assignments_required"]

    # NOE constraints: list of (p1, a1, p2, a2) meaning
    # x[p1,a1] + x[p2,a2] <= 1
    # From the problem description:
    # If Peak 0 -> AA0, Peak 1 cannot be AA2, AA3, AA4
    # If Peak 0 -> AA1, Peak 1 cannot be AA2, AA3, AA4
    noe_incompatible = [
        (0, 0, 1, 2),
        (0, 0, 1, 3),
        (0, 0, 1, 4),
        (0, 1, 1, 2),
        (0, 1, 1, 3),
        (0, 1, 1, 4),
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[p, a] = 1 if peak p assigned to amino acid a
    x = {}
    for p in range(num_peaks):
        for a in range(num_aas):
            x[(p, a)] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{a}")

    model.update()

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[(p, a)] * x[(p, a)] for p in range(num_peaks) for a in range(num_aas)),
        GRB.MINIMIZE
    )

    # Each peak assigned to at most one amino acid
    for p in range(num_peaks):
        model.addConstr(
            gp.quicksum(x[(p, a)] for a in range(num_aas)) <= 1,
            name=f"peak_{p}_at_most_one"
        )

    # Each amino acid assigned to at most one peak
    for a in range(num_aas):
        model.addConstr(
            gp.quicksum(x[(p, a)] for p in range(num_peaks)) <= 1,
            name=f"aa_{a}_at_most_one"
        )

    # Exactly num_assignments_required assignments total
    model.addConstr(
        gp.quicksum(x[(p, a)] for p in range(num_peaks) for a in range(num_aas)) == num_assignments_required,
        name="total_assignments"
    )

    # NOE incompatibility constraints
    for idx, (p1, a1, p2, a2) in enumerate(noe_incompatible):
        model.addConstr(
            x[(p1, a1)] + x[(p2, a2)] <= 1,
            name=f"noe_{idx}"
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