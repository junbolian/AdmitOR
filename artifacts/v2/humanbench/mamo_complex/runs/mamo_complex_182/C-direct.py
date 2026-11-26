import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_costs = params["opening_costs"]      # list of 9 values
    transport_costs = params["transport_costs"]  # 9x8 matrix
    demands = params["demands"]                  # list of 8 values
    capacities = params["capacities"]            # list of 9 values

    num_dc = 9
    num_stores = 8

    model = gp.Model("MegaMart_Distribution")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i] = 1 if DC i is opened
    y = model.addVars(num_dc, vtype=GRB.BINARY, name="y")
    # x[i][j] = units shipped from DC i to store j
    x = model.addVars(num_dc, num_stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_costs[i] * y[i] for i in range(num_dc)) +
        gp.quicksum(transport_costs[i][j] * x[i, j]
                    for i in range(num_dc) for j in range(num_stores)),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_dc)) >= demands[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from DC i cannot exceed its capacity if open,
    # and must be zero if closed
    for i in range(num_dc):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_stores)) <= capacities[i] * y[i],
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