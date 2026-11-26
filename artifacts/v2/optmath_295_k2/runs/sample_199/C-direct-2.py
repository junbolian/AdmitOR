import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_demand = params["supply_demand"]
    cost_matrix_flat = params["cost_matrix"]
    capacity_matrix_flat = params["capacity_matrix"]
    n = params["num_cities"]

    cost = {}
    capacity = {}

    full_size = n * n
    skip_diag_size = n * (n - 1)

    if len(cost_matrix_flat) == full_size:
        # Full n×n matrix, diagonal entries present (ignored)
        for i in range(n):
            for j in range(n):
                if i != j:
                    cost[(i, j)] = cost_matrix_flat[i * n + j]
                    capacity[(i, j)] = capacity_matrix_flat[i * n + j]
    elif len(cost_matrix_flat) == skip_diag_size:
        # Row-major skipping diagonal
        idx = 0
        for i in range(n):
            for j in range(n):
                if i != j:
                    cost[(i, j)] = cost_matrix_flat[idx]
                    capacity[(i, j)] = capacity_matrix_flat[idx]
                    idx += 1
    else:
        return {"objective": None, "status": f"unexpected cost_matrix length {len(cost_matrix_flat)}"}

    model = gp.Model("transport")
    model.setParam("OutputFlag", 0)

    flow = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                flow[(i, j)] = model.addVar(
                    lb=0.0,
                    ub=capacity[(i, j)],
                    obj=cost[(i, j)],
                    vtype=GRB.CONTINUOUS,
                    name=f"flow_{i}_{j}"
                )

    model.ModelSense = GRB.MINIMIZE

    for i in range(n):
        inflow = gp.quicksum(flow[(j, i)] for j in range(n) if j != i)
        outflow = gp.quicksum(flow[(i, j)] for j in range(n) if j != i)
        # supply_demand[i] > 0 means surplus (net outflow): outflow - inflow = supply_demand[i]
        # equivalently: inflow - outflow = -supply_demand[i]
        model.addConstr(inflow - outflow == -supply_demand[i], name=f"balance_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}