import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_peaks = 5
    num_aas = 6

    cost = {}
    for p in range(num_peaks):
        for a in range(num_aas):
            key = f"cost_peak{p}_aa{a}"
            cost[(p, a)] = params[key]

    num_required = params["num_assignments_required"]
    noe_rhs_1 = params["noe_pair_p1aa1_p2aa0_rhs"]
    noe_rhs_2 = params["noe_pair_p1aa3_p2aa0_rhs"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_peaks, num_aas, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[(p, a)] * x[p, a] for p in range(num_peaks) for a in range(num_aas)),
        GRB.MINIMIZE
    )

    # Each peak assigned to at most one amino acid
    for p in range(num_peaks):
        model.addConstr(gp.quicksum(x[p, a] for a in range(num_aas)) <= 1, name=f"peak_{p}_once")

    # Each amino acid receives at most one peak
    for a in range(num_aas):
        model.addConstr(gp.quicksum(x[p, a] for p in range(num_peaks)) <= 1, name=f"aa_{a}_once")

    # Exactly num_required assignments total
    model.addConstr(
        gp.quicksum(x[p, a] for p in range(num_peaks) for a in range(num_aas)) == num_required,
        name="total_assignments"
    )

    # NOE constraints
    # x(P1, AA1) + x(P2, AA0) <= noe_rhs_1
    model.addConstr(x[1, 1] + x[2, 0] <= noe_rhs_1, name="noe_p1aa1_p2aa0")
    # x(P1, AA3) + x(P2, AA0) <= noe_rhs_2
    model.addConstr(x[1, 3] + x[2, 0] <= noe_rhs_2, name="noe_p1aa3_p2aa0")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}