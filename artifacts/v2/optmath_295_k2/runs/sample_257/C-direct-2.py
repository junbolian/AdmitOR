import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 8
    nodes = list(range(n))
    
    # Build cost dict from params
    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                key = f"c_{i}_{j}"
                if key in params:
                    cost[(i, j)] = params[key]
    
    supply_node0 = params["supply_node0"]
    demand_node7 = params["demand_node7"]
    
    # Net supply/demand at each node
    # Node 0: net outflow = supply_node0 (positive supply)
    # Node 7: net inflow = demand_node7 (positive demand)
    # Others: 0
    b = {node: 0.0 for node in nodes}
    b[0] = supply_node0    # net supply at node 0
    b[7] = -demand_node7   # net demand at node 7
    
    arcs = list(cost.keys())
    
    model = gp.Model("shortest_path")
    model.setParam("OutputFlag", 0)
    
    # Binary flow variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")
    
    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[(i, j)] * x[(i, j)] for (i, j) in arcs), GRB.MINIMIZE)
    
    # Flow balance constraints
    for node in nodes:
        outflow = gp.quicksum(x[(i, j)] for (i, j) in arcs if i == node)
        inflow = gp.quicksum(x[(i, j)] for (i, j) in arcs if j == node)
        # outflow - inflow = b[node]
        model.addConstr(outflow - inflow == b[node], name=f"balance_{node}")
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}