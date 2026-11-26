import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    supply_capacities = params["supply_capacities"]

    num_centers = len(opening_costs)
    num_stores = len(demands)

    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)

    # Binary variable: open center i
    y = model.addVars(centers, vtype=GRB.BINARY, name="y")

    # Continuous variable: units shipped from center i to store j
    x = model.addVars(centers, stores, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_costs[i] * y[i] for i in centers) +
        gp.quicksum(transport_costs[i][j] * x[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in centers) >= demands[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: total shipped from center i cannot exceed its capacity if open
    for i in centers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in stores) <= supply_capacities[i] * y[i],
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