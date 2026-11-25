def solve(params):
    """
    Solve the minimum cost transportation problem using Gurobi.
    
    Args:
        params: dict with keys 'supply', 'demand', 'cost', 'capacity'
        
    Returns:
        dict with 'objective' (float or None) and 'status' (str)
    """
    import gurobipy as gp
    from gurobipy import GRB
    
    # Extract parameters
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]
    
    num_origins = len(supply)
    num_destinations = len(demand)
    
    # Create model
    model = gp.Model("transportation")
    model.Params.OutputFlag = 0  # Suppress output
    
    # Decision variables: x[i,j] = units transported from origin i to destination j
    x = {}
    for i in range(num_origins):
        for j in range(num_destinations):
            x[i, j] = model.addVar(
                lb=0,
                ub=capacity[i][j],
                name=f"x_{i}_{j}"
            )
    
    model.update()
    
    # Objective: minimize total transportation cost
    obj = gp.quicksum(
        cost[i][j] * x[i, j]
        for i in range(num_origins)
        for j in range(num_destinations)
    )
    model.setObjective(obj, GRB.MINIMIZE)
    
    # Supply constraints: all supply from each origin must be sent
    for i in range(num_origins):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_destinations)) == supply[i],
            name=f"supply_{i}"
        )
    
    # Demand constraints: each destination must receive exactly its demand
    for j in range(num_destinations):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_origins)) == demand[j],
            name=f"demand_{j}"
        )
    
    # Optimize
    model.optimize()
    
    # Extract results
    if model.status == GRB.OPTIMAL:
        return {
            "objective": model.objVal,
            "status": "optimal"
        }
    elif model.status == GRB.INFEASIBLE:
        return {
            "objective": None,
            "status": "infeasible"
        }
    elif model.status == GRB.UNBOUNDED:
        return {
            "objective": None,
            "status": "unbounded"
        }
    else:
        return {
            "objective": None,
            "status": f"solver_status_{model.status}"
        }