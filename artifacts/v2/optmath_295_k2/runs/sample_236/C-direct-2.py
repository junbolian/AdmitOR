def solve(params):
    import gurobipy as gp
    from gurobipy import GRB
    
    # Extract parameters
    bin_capacity = params["bin_capacity"]
    item_weights = [params[f"item_weight_{i}"] for i in range(7)]
    
    n_items = 7
    n_bins = 7  # Upper bound on number of bins needed
    
    # Create model
    model = gp.Model("warehouse_packing")
    model.Params.OutputFlag = 0  # Suppress output
    
    # Decision variables
    # bin_used[j] = 1 if bin j is used, 0 otherwise
    bin_used = model.addVars(n_bins, vtype=GRB.BINARY, name="bin_used")
    
    # assignment[i, j] = 1 if item i is assigned to bin j, 0 otherwise
    assignment = model.addVars(n_items, n_bins, vtype=GRB.BINARY, name="assignment")
    
    # Objective: minimize number of bins used
    model.setObjective(bin_used.sum(), GRB.MINIMIZE)
    
    # Constraint 1: Each item must be assigned to exactly one bin
    for i in range(n_items):
        model.addConstr(
            gp.quicksum(assignment[i, j] for j in range(n_bins)) == 1,
            f"item_assignment_{i}"
        )
    
    # Constraint 2: Bin capacity constraint
    for j in range(n_bins):
        model.addConstr(
            gp.quicksum(item_weights[i] * assignment[i, j] for i in range(n_items)) <= bin_capacity,
            f"capacity_{j}"
        )
    
    # Constraint 3: Bin activation constraint
    # If any items are assigned to bin j, then bin j must be used
    for j in range(n_bins):
        model.addConstr(
            gp.quicksum(assignment[i, j] for i in range(n_items)) <= n_items * bin_used[j],
            f"activate_{j}"
        )
    
    # Optimize
    model.optimize()
    
    # Return result based on optimization status
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
    else:
        return {
            "objective": None,
            "status": f"failed_status_{model.status}"
        }