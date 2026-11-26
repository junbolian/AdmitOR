import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_centers = 8
    n_stores = 9

    model = gp.Model("logichain")
    model.setParam("OutputFlag", 0)

    # Binary variable: open center i
    y = model.addVars(n_centers, vtype=GRB.BINARY, name="y")

    # Continuous variable: units shipped from center i to store j
    x = model.addVars(n_centers, n_stores, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_costs[i] * y[i] for i in range(n_centers)) +
        gp.quicksum(transport_costs[i][j] * x[i, j] for i in range(n_centers) for j in range(n_stores)),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in range(n_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_centers)) == demands[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from center i cannot exceed its capacity (only if open)
    for i in range(n_centers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_stores)) <= capacities[i] * y[i],
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