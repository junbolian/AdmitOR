import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    num_facilities = params["num_facilities"]
    num_dcs = params["num_dcs"]

    # Build cost and capacity dictionaries from params
    # Only specific costs/caps are provided; for others we need defaults
    # The problem states costs/caps are "similarly specified in the LP data"
    # We'll read named ones from params and use a default for the rest
    # Since only specific pairs are in params, we need to handle missing ones
    # The problem implies all pairs exist - we'll use a large default cost for missing
    # and large cap for missing caps (effectively uncapped relative to supply)
    
    cost = {}
    cap = {}
    
    for i in range(num_facilities):
        for j in range(num_dcs):
            cost_key = f"cost_{i}_{j}"
            cap_key = f"cap_{i}_{j}"
            if cost_key in params:
                cost[i, j] = params[cost_key]
            else:
                # Default cost - use a high but finite value
                cost[i, j] = 100  # large default cost
            if cap_key in params:
                cap[i, j] = params[cap_key]
            else:
                # Default cap - unconstrained (use total supply as upper bound)
                cap[i, j] = sum(supply)

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    # Decision variables
    x = {}
    for i in range(num_facilities):
        for j in range(num_dcs):
            x[i, j] = model.addVar(lb=0.0, ub=cap[i, j], name=f"x_{i}_{j}")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in range(num_facilities) for j in range(num_dcs)),
        GRB.MINIMIZE
    )

    # Supply constraints: each facility distributes exactly its supply
    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_dcs)) == supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints: each DC receives exactly its demand
    for j in range(num_dcs):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_facilities)) == demand[j],
            name=f"demand_{j}"
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