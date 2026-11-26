import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]    # list of 4 values
    transport_cost = params["transport_cost"]  # 4x8 list of lists
    demand = params["demand"]                # list of 8 values
    capacity = params["capacity"]            # list of 4 values

    num_centers = len(opening_cost)
    num_stores = len(demand)

    model = gp.Model("logichain")
    model.setParam("OutputFlag", 0)

    # Binary variable: open center i
    open_var = model.addVars(num_centers, vtype=GRB.BINARY, name="open")

    # Continuous variable: units shipped from center i to store j
    ship = model.addVars(num_centers, num_stores, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * open_var[i] for i in range(num_centers)) +
        gp.quicksum(transport_cost[i][j] * ship[i, j]
                    for i in range(num_centers) for j in range(num_stores)),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(num_centers)) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from a center cannot exceed its capacity (if open)
    for i in range(num_centers):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(num_stores)) <= capacity[i] * open_var[i],
            name=f"capacity_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}