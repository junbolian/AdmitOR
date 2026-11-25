import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 11  # number of hubs (structural constant)
    
    # Build cost dictionary from params
    cost = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                key = f"cost_{i}_{j}"
                if key in params:
                    cost[(i, j)] = params[key]
    
    supply_hub0 = params["supply_hub0"]
    demand_hub10 = params["demand_hub10"]
    
    model = gp.Model("min_cost_flow")
    model.setParam("OutputFlag", 0)
    
    # Binary flow variables for each valid arc
    arcs = list(cost.keys())
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")
    
    # Objective: minimize total transportation cost
    model.setObjective(gp.quicksum(cost[a] * x[a] for a in arcs), GRB.MINIMIZE)
    
    # Flow balance constraints
    for node in range(n):
        outflow = gp.quicksum(x[(i, j)] for (i, j) in arcs if i == node)
        inflow = gp.quicksum(x[(i, j)] for (i, j) in arcs if j == node)
        if node == 0:
            model.addConstr(outflow - inflow == supply_hub0, name=f"balance_{node}")
        elif node == 10:
            model.addConstr(inflow - outflow == demand_hub10, name=f"balance_{node}")
        else:
            model.addConstr(outflow - inflow == 0, name=f"balance_{node}")
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}