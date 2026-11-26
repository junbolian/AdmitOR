import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_costs = params["opening_costs"]   # list of length 4
    transport_costs = params["transport_costs"]  # list of 4 lists, each of length 6
    demands = params["demands"]               # list of length 6
    capacities = params["capacities"]         # list of length 4

    num_centers = 4
    num_stores = 6

    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model("MarketFlow")
    model.setParam("OutputFlag", 0)

    # Binary variable: open center i
    open_vars = model.addVars(centers, vtype=GRB.BINARY, name="open")

    # Continuous variable: units shipped from center i to store j
    ship_vars = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_costs[i] * open_vars[i] for i in centers) +
        gp.quicksum(transport_costs[i][j] * ship_vars[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(ship_vars[i, j] for i in centers) == demands[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from a center cannot exceed its capacity (and 0 if closed)
    for i in centers:
        model.addConstr(
            gp.quicksum(ship_vars[i, j] for j in stores) <= capacities[i] * open_vars[i],
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}