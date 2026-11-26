import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 5
    nodes = list(range(1, n + 1))
    
    # Build cost matrix from params
    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]
    
    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)
    
    # Binary variables: x[i,j] = 1 if travel from i to j
    x = model.addVars(
        [(i, j) for i in nodes for j in nodes if i != j],
        vtype=GRB.BINARY,
        name="x"
    )
    
    # MTZ subtour elimination variables
    u = model.addVars(nodes, vtype=GRB.CONTINUOUS, name="u")
    
    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )
    
    # Each node is left exactly once
    for i in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for j in nodes if j != i) == 1,
            name=f"leave_{i}"
        )
    
    # Each node is entered exactly once
    for j in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
            name=f"enter_{j}"
        )
    
    # MTZ subtour elimination constraints
    for i in nodes:
        for j in nodes:
            if i != j and j != 1:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name=f"mtz_{i}_{j}"
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