import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    num_assignments = params["num_assignments"]
    num_peaks = params["num_peaks"]
    num_amino_acids = params["num_amino_acids"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_peaks, num_amino_acids, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)),
        GRB.MINIMIZE
    )

    for i in range(num_peaks):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_amino_acids)) <= 1)

    for j in range(num_amino_acids):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1)

    model.addConstr(
        gp.quicksum(x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)) == num_assignments
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}