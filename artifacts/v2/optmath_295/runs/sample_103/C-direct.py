import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    num_assignments = params["num_assignments"]
    num_peaks = params["num_peaks"]
    num_amino_acids = params["num_amino_acids"]

    peaks = range(num_peaks)
    amino_acids = range(num_amino_acids)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(peaks, amino_acids, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[p][a] * x[p, a] for p in peaks for a in amino_acids),
        GRB.MINIMIZE
    )

    # Each peak assigned to at most one amino acid
    for p in peaks:
        model.addConstr(gp.quicksum(x[p, a] for a in amino_acids) <= 1)

    # Each amino acid assigned to at most one peak
    for a in amino_acids:
        model.addConstr(gp.quicksum(x[p, a] for p in peaks) <= 1)

    # Exactly num_assignments assignments total
    model.addConstr(gp.quicksum(x[p, a] for p in peaks for a in amino_acids) == num_assignments)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}