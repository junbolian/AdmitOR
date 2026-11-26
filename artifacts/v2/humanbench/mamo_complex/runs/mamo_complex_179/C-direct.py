import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]      # list of length n_dc
    transport_cost = params["transport_cost"]  # list of lists [n_dc][n_store]
    store_demand = params["store_demand"]      # list of length n_store
    dc_capacity = params["dc_capacity"]        # list of length n_dc

    n_dc = len(opening_cost)
    n_store = len(store_demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[i] = 1 if DC i is opened
    y = model.addVars(n_dc, vtype=GRB.BINARY, name="y")

    # x[i, j] = units shipped from DC i to store j
    x = model.addVars(n_dc, n_store, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in range(n_dc)) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in range(n_dc) for j in range(n_store)),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be met
    for j in range(n_store):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_dc)) >= store_demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: DC i can only ship up to its capacity if opened
    for i in range(n_dc):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_store)) <= dc_capacity[i] * y[i],
            name=f"capacity_{i}"
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