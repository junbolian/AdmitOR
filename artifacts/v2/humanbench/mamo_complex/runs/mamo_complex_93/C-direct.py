import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]
    n_centers = params["n_centers"]
    n_stores = params["n_stores"]

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i] = 1 if center i is opened
    y = model.addVars(n_centers, vtype=GRB.BINARY, name="y")

    # x[i, j] = units shipped from center i to store j
    x = model.addVars(n_centers, n_stores, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    # transport_costs[i] is [min_cost, max_cost] for center i
    # We use the minimum transport cost per unit as the lower bound on cost,
    # but since exact per-store costs are not given, we model using the
    # per-row bounds as constraints on the per-unit cost from each center.
    # We introduce auxiliary variables c[i,j] representing the actual unit
    # transport cost from center i to store j, bounded by [min_i, max_i].
    
    c = model.addVars(n_centers, n_stores, name="c")

    for i in range(n_centers):
        t_min = transport_costs[i][0]
        t_max = transport_costs[i][1]
        for j in range(n_stores):
            model.addConstr(c[i, j] >= t_min)
            model.addConstr(c[i, j] <= t_max)

    # Total cost = sum of opening costs for opened centers + sum of transport cost * units
    # Transportation cost term: sum_i sum_j c[i,j] * x[i,j]
    # This is bilinear; to minimize, the optimizer will drive c[i,j] to its minimum
    # since c appears linearly with positive coefficient x[i,j] >= 0.
    # So effectively c[i,j] = t_min[i] at optimum — but we model it properly.
    # Since minimizing over c[i,j] with x[i,j] >= 0 will set c[i,j] = t_min[i],
    # we can simplify by using t_min directly. However, to stay faithful to the
    # problem structure (bounded ranges), we use the min cost (optimizer will choose it).
    
    # Actually, since c[i,j] * x[i,j] is bilinear, we need to linearize or note
    # that at optimality c[i,j] = t_min[i]. Let's just use t_min directly for a
    # linear model, as the problem says costs vary per store within [min, max].
    # The optimal strategy minimizes cost, so use min transport cost.
    
    # Re-model cleanly: use t_min as the transport cost (minimum possible, optimizer's choice)
    transport_obj = gp.quicksum(
        transport_costs[i][0] * x[i, j]
        for i in range(n_centers)
        for j in range(n_stores)
    )

    opening_obj = gp.quicksum(opening_costs[i] * y[i] for i in range(n_centers))

    model.setObjective(opening_obj + transport_obj, GRB.MINIMIZE)

    # Demand constraints: each store's demand must be fully met
    for j in range(n_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_centers)) == demands[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: opened center cannot exceed its capacity
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