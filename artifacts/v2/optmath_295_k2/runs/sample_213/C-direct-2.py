import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 5
    nodes = range(n)
    
    # Build weight matrix from params
    weights = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                weights[(i, j)] = params[f"weight_{i}_{j}"]
    
    selection_count = params["selection_count"]
    
    model = gp.Model("facility_dispersion")
    model.setParam("OutputFlag", 0)
    
    # Binary variable: x[i] = 1 if facility i is selected
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")
    
    # Binary variable: z[i,j] = 1 if both i and j are selected
    pairs = [(i, j) for i in nodes for j in nodes if i != j]
    z = model.addVars(pairs, vtype=GRB.BINARY, name="z")
    
    # Objective: maximize total weighted dispersion
    model.setObjective(
        gp.quicksum(weights[(i, j)] * z[i, j] for (i, j) in pairs),
        GRB.MAXIMIZE
    )
    
    # Constraint: select exactly selection_count facilities
    model.addConstr(gp.quicksum(x[i] for i in nodes) == selection_count, name="select_count")
    
    # Pairwise activation constraints
    for (i, j) in pairs:
        # z[i,j] <= x[i]
        model.addConstr(z[i, j] <= x[i], name=f"act_i_{i}_{j}")
        # z[i,j] <= x[j]
        model.addConstr(z[i, j] <= x[j], name=f"act_j_{i}_{j}")
        # z[i,j] >= x[i] + x[j] - 1
        model.addConstr(z[i, j] >= x[i] + x[j] - 1, name=f"act_both_{i}_{j}")
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}