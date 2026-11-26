import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_demand = params["supply_demand"]
    cost_matrix_raw = params["cost_matrix"]
    capacity_matrix_raw = params["capacity_matrix"]
    num_cities = params["num_cities"]

    # Reconstruct cost and capacity dicts
    # The matrices may be 2D lists (num_cities x num_cities-1) or flat row-major skipping diagonal
    # Determine format: if it's a list of lists, treat as 2D; otherwise treat as flat
    cost = {}
    capacity = {}

    if isinstance(cost_matrix_raw[0], (list, tuple)):
        # 2D list: row i has num_cities-1 entries (skipping diagonal)
        for i in range(num_cities):
            col_idx = 0
            for j in range(num_cities):
                if i != j:
                    cost[(i, j)] = cost_matrix_raw[i][col_idx]
                    capacity[(i, j)] = capacity_matrix_raw[i][col_idx]
                    col_idx += 1
    else:
        # Flat list, row-major, skipping diagonal
        idx = 0
        for i in range(num_cities):
            for j in range(num_cities):
                if i != j:
                    cost[(i, j)] = cost_matrix_raw[idx]
                    capacity[(i, j)] = capacity_matrix_raw[idx]
                    idx += 1

    model = gp.Model("transport")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow from i to j
    flow = {}
    for i in range(num_cities):
        for j in range(num_cities):
            if i != j:
                flow[(i, j)] = model.addVar(
                    lb=0.0,
                    ub=capacity[(i, j)],
                    obj=cost[(i, j)],
                    vtype=GRB.CONTINUOUS,
                    name=f"flow_{i}_{j}"
                )

    model.ModelSense = GRB.MINIMIZE

    # Flow balance: inflow - outflow = -supply_demand[i]
    # Positive supply_demand means surplus (net outflow), negative means demand (net inflow)
    for i in range(num_cities):
        inflow = gp.quicksum(flow[(j, i)] for j in range(num_cities) if j != i)
        outflow = gp.quicksum(flow[(i, j)] for j in range(num_cities) if j != i)
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