def solve(params):
    import gurobipy as gp
    from gurobipy import GRB
    
    model = gp.Model("MaxFlow")
    model.Params.OutputFlag = 0
    
    # Define hubs
    hubs = list(range(7))
    source = 0
    sink = 6
    
    # Build edge list from params with capacities
    edges = []
    capacity_map = {}
    
    # Extract all capacity parameters
    for i in hubs:
        for j in hubs:
            if i != j:
                param_name = f"cap_{i}_{j}"
                if param_name in params:
                    cap = params[param_name]
                    if cap > 0:
                        edges.append((i, j))
                        capacity_map[(i, j)] = cap
    
    # Create flow variables for each edge
    flow = model.addVars(edges, name="flow", lb=0)
    
    # Add capacity constraints
    for edge in edges:
        model.addConstr(flow[edge] <= capacity_map[edge], 
                       name=f"cap_{edge[0]}_{edge[1]}")
    
    # Add flow conservation constraints
    for hub in hubs:
        if hub == source:
            # Outflow from source minus inflow = total flow out
            outflow = gp.quicksum(flow[e] for e in edges if e[0] == source)
            inflow = gp.quicksum(flow[e] for e in edges if e[1] == source)
            model.addConstr(outflow - inflow == gp.quicksum(flow[e] for e in edges if e[0] == source and e[1] == sink),
                           name=f"balance_{hub}")
        elif hub == sink:
            # Inflow to sink minus outflow = total flow in
            inflow = gp.quicksum(flow[e] for e in edges if e[1] == sink)
            outflow = gp.quicksum(flow[e] for e in edges if e[0] == sink)
            model.addConstr(inflow - outflow == gp.quicksum(flow[e] for e in edges if e[1] == sink),
                           name=f"balance_{hub}")
        else:
            # Intermediate hubs: inflow = outflow
            outflow = gp.quicksum(flow[e] for e in edges if e[0] == hub)
            inflow = gp.quicksum(flow[e] for e in edges if e[1] == hub)
            model.addConstr(inflow == outflow, name=f"balance_{hub}")
    
    # Objective: maximize flow to sink
    total_flow = gp.quicksum(flow[e] for e in edges if e[1] == sink)
    model.setObjective(total_flow, GRB.MAXIMIZE)
    
    # Solve
    model.optimize()
    
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
            "status": "failed"
        }