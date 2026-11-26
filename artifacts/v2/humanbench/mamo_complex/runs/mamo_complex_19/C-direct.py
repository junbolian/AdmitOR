import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_costs = params["opening_costs"]
    transportation_costs = params["transportation_costs"]
    demands = params["demands"]
    capacities = params["capacities"]
    num_centers = params["num_centers"]
    num_stores = params["num_stores"]

    model = gp.Model("SupplyTek")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i] = 1 if distribution center i is opened
    y = model.addVars(num_centers, vtype=GRB.BINARY, name="y")
    # x[i][j] = units shipped from center i to store j
    x = model.addVars(num_centers, num_stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize total opening cost + transportation cost
    model.setObjective(
        gp.quicksum(opening_costs[i] * y[i] for i in range(num_centers)) +
        gp.quicksum(transportation_costs[i][j] * x[i, j]
                    for i in range(num_centers) for j in range(num_stores)),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_centers)) >= demands[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from center i cannot exceed its capacity if open
    for i in range(num_centers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_stores)) <= capacities[i] * y[i],
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