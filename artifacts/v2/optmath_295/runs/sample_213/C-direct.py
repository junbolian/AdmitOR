import gurobipy as gp
from gurobipy import GRB

def solve(params):
    dispersion_weights = params["dispersion_weights"]
    num_facilities = params["num_facilities_to_select"]
    n = params["num_locations"]

    # Build weight matrix from flattened row-major input
    w = {}
    for i in range(n):
        for j in range(n):
            w[i, j] = dispersion_weights[i * n + j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if location i is selected
    x = model.addVars(n, vtype=GRB.BINARY, name="x")

    # y[i,j] = 1 if both i and j are selected (pairwise activation)
    y = model.addVars(n, n, vtype=GRB.BINARY, name="y")

    # Objective: maximize total weighted dispersion over all ordered pairs (i != j)
    model.setObjective(
        gp.quicksum(w[i, j] * y[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MAXIMIZE
    )

    # Exactly num_facilities locations selected
    model.addConstr(gp.quicksum(x[i] for i in range(n)) == num_facilities, name="select_count")

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            # y[i,j] <= x[i]
            model.addConstr(y[i, j] <= x[i], name=f"act_i_{i}_{j}")
            # y[i,j] <= x[j]
            model.addConstr(y[i, j] <= x[j], name=f"act_j_{i}_{j}")
            # y[i,j] >= x[i] + x[j] - 1
            model.addConstr(y[i, j] >= x[i] + x[j] - 1, name=f"act_lb_{i}_{j}")

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