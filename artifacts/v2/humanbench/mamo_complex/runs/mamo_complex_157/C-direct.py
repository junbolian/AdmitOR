def solve(params):
    import gurobipy as gp
    from gurobipy import GRB
    
    model = gp.Model("MaxFlow")
    
    nodes = list(range(7))
    source = 0
    sink = 6
    
    # Create flow variables for all edges present in params
    flow = {}
    for i in range(7):
        for j in range(7):
            if i != j:
                cap_key = f"capacity_{i}_{j}"
                if cap_key in params:
                    flow[(i, j)] = model.addVar(lb=0, name=f"flow_{i}_{j}")
    
    # Capacity constraints
    for (i, j), var in flow.items():
        cap_key = f"capacity_{i}_{j}"
        model.addConstr(var <= params[cap_key], name=f"cap_{i}_{j}")
    
    # Flow conservation constraints
    for node in nodes:
        outgoing = gp.quicksum(flow[(i, j)] for (i, j) in flow if i == node)
        incoming = gp.quicksum(flow[(i, j)] for (i, j) in flow if j == node)
        
        if node == source:
            # Source: net outflow
            model.addConstr(outgoing - incoming >= 0, name=f"balance_{node}")
        elif node == sink:
            # Sink: net inflow
            model.addConstr(incoming - outgoing >= 0, name=f"balance_{node}")
        else:
            # Intermediate nodes: flow conservation
            model.addConstr(incoming == outgoing, name=f"balance_{node}")
    
    # Objective: maximize flow entering the sink
    total_inflow_to_sink = gp.quicksum(
        flow[(i, j)] for (i, j) in flow if j == sink
    )
    model.setObjective(total_inflow_to_sink, GRB.MAXIMIZE)
    
    model.optimize()
    
    if model.status == GRB.OPTIMAL:
        return {"objective": model.objVal, "status": "optimal"}
    else:
        status_lookup = {
            GRB.INFEASIBLE: "infeasible",
            GRB.UNBOUNDED: "unbounded",
            GRB.INF_OR_UNBD: "infeasible_or_unbounded",
            GRB.SUBOPTIMAL: "suboptimal"
        }
        reason = status_lookup.get(model.status, "failed")
        return {"objective": None, "status": reason}