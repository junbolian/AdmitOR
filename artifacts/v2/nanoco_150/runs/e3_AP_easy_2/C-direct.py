import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    n_drivers = len(cost_matrix)
    n_rides = len(cost_matrix[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_drivers, n_rides, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in range(n_drivers) for j in range(n_rides)),
        GRB.MINIMIZE
    )

    for i in range(n_drivers):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n_rides)) == 1, name=f"driver_{i}")

    for j in range(n_rides):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n_drivers)) == 1, name=f"ride_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}