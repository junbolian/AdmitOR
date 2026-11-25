import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    n_vms = len(cost_matrix)
    n_nodes = len(cost_matrix[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables: x[i,j] = 1 if VM i assigned to node j
    x = model.addVars(n_vms, n_nodes, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in range(n_vms) for j in range(n_nodes)),
        GRB.MINIMIZE
    )

    # Each VM assigned to exactly one node
    for i in range(n_vms):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n_nodes)) == 1, name=f"vm_{i}")

    # Each node hosts exactly one VM
    for j in range(n_nodes):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n_vms)) == 1, name=f"node_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}