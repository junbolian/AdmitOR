import gurobipy as gp
from gurobipy import GRB

def solve(params):
    net_supply = params["net_supply"]
    
    # Define all directed arcs (i, j) where i != j, for 7 cities
    n = 7
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    
    # Build cost and capacity dicts from params
    cost = {}
    cap = {}
    for (i, j) in arcs:
        cost[(i, j)] = params[f"cost_{i}_{j}"]
        cap[(i, j)] = params[f"cap_{i}_{j}"]
    
    model = gp.Model("min_cost_flow")
    model.setParam("OutputFlag", 0)
    
    # Decision variables: flow on each arc
    flow = model.addVars(arcs, lb=0.0, name="flow")
    
    # Capacity constraints
    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")
    
    # Flow balance constraints: outflow - inflow = net_supply[i]
    for i in range(n):
        outflow = gp.quicksum(flow[i, j] for j in range(n) if i != j)
        inflow = gp.quicksum(flow[j, i] for j in range(n) if i != j)
        model.addConstr(outflow - inflow == net_supply[i], name=f"balance_{i}")
    
    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * flow[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
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