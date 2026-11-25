import gurobipy as gp
from gurobipy import GRB

def solve(params):
    weights_list = params["weights"]
    
    # 5 nodes, ordered pairs (i,j) for i != j
    # weights_list ordering: (0,1),(0,2),(0,3),(0,4),(1,0),(1,2),(1,3),(1,4),(2,0),(2,1),(2,3),(2,4),(3,0),(3,1),(3,2),(3,4),(4,0),(4,1),(4,2),(4,3)
    n = 5
    ordered_pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    w = {ordered_pairs[k]: weights_list[k] for k in range(len(ordered_pairs))}
    
    model = gp.Model()
    model.setParam("OutputFlag", 0)
    
    # Binary variable: x[i] = 1 if node i is selected
    x = model.addVars(n, vtype=GRB.BINARY, name="x")
    
    # Binary variable: y[i,j] = 1 if both i and j are selected
    y = model.addVars(ordered_pairs, vtype=GRB.BINARY, name="y")
    
    # Exactly 3 facilities
    model.addConstr(gp.quicksum(x[i] for i in range(n)) == 3, name="select_three")
    
    # Linearization constraints: y[i,j] <= x[i], y[i,j] <= x[j], y[i,j] >= x[i] + x[j] - 1
    for (i, j) in ordered_pairs:
        model.addConstr(y[i, j] <= x[i], name=f"y_xi_{i}_{j}")
        model.addConstr(y[i, j] <= x[j], name=f"y_xj_{i}_{j}")
        model.addConstr(y[i, j] >= x[i] + x[j] - 1, name=f"y_lb_{i}_{j}")
    
    # Objective: maximize total dispersion
    model.setObjective(
        gp.quicksum(w[i, j] * y[i, j] for (i, j) in ordered_pairs),
        GRB.MAXIMIZE
    )
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}