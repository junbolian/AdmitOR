import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost = params["cost"]

    num_peaks = len(cost)
    num_amino = len(cost[0]) if num_peaks > 0 else 0

    model = gp.Model("nmr_assignment")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(num_peaks):
        for j in range(num_amino):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_peaks) for j in range(num_amino)),
        GRB.MINIMIZE,
    )

    # Each peak assigned to at most one amino acid
    for i in range(num_peaks):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_amino)) <= 1, name=f"peak_{i}")

    # Each amino acid assigned to at most one peak
    for j in range(num_amino):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1, name=f"amino_{j}")

    # Exactly two assignments in total
    model.addConstr(
        gp.quicksum(x[i, j] for i in range(num_peaks) for j in range(num_amino)) == 2,
        name="total_assignments",
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    return {"objective": None, "status": f"status_{model.status}"}