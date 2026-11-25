import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 8
    nodes = list(range(n))
    
    # Build cost dictionary from params
    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                key = f"c_{i}_{j}"
                if key in params:
                    cost[(i, j)] = params[key]
    
    arcs = list(cost.keys())
    
    model = gp.Model("shortest_path")
    model.setParam("OutputFlag", 0)
    
    # Binary flow variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")
    
    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[a] * x[a] for a in arcs), GRB.MINIMIZE)
    
    supply_0 = params["supply_node0"]
    demand_7 = params["demand_node7"]
    
    # Flow balance constraints
    for node in nodes:
        inflow = gp.quicksum(x[(i, j)] for (i, j) in arcs if j == node)
        outflow = gp.quicksum(x[(i, j)] for (i, j) in arcs if i == node)
        
        if node == 0:
            # Net outflow = supply_node0
            model.addConstr(outflow - inflow == supply_0, name=f"balance_{node}")
        elif node == 7:
            # Net inflow = demand_node7
            model.addConstr(inflow - outflow == demand_7, name=f"balance_{node}")
        else:
            # Flow conservation
            model.addConstr(inflow == outflow, name=f"balance_{node}")
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}