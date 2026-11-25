import gurobipy as gp
from gurobipy import GRB

def solve(params):
    factories = list(range(6))
    months = list(range(4))
    
    # Create model
    model = gp.Model("multi_factory_production")
    model.setParam('OutputFlag', 0)
    
    # Decision variables
    # Binary variables: whether factory f runs in month t
    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")
    
    # Continuous variables: production level at factory f in month t
    prod = model.addVars(factories, months, vtype=GRB.CONTINUOUS, lb=0, name="prod")
    
    # Extract parameters
    fixed_cost = {}
    for f in factories:
        for t in months:
            fixed_cost[f, t] = params[f"fixed_cost_f{f}_month{t}"]
    
    var_cost = {}
    for f in factories:
        var_cost[f] = params[f"var_cost_f{f}"]
    
    min_prod = {}
    max_prod = {}
    for f in factories:
        min_prod[f] = params[f"min_prod_f{f}"]
        max_prod[f] = params[f"max_prod_f{f}"]
    
    demand = {}
    for t in months:
        demand[t] = params[f"demand_month{t}"]
    
    # Objective: minimize total cost
    total_fixed_cost = gp.quicksum(fixed_cost[f, t] * run[f, t] 
                                    for f in factories for t in months)
    total_var_cost = gp.quicksum(var_cost[f] * prod[f, t] 
                                  for f in factories for t in months)
    model.setObjective(total_fixed_cost + total_var_cost, GRB.MINIMIZE)
    
    # Constraints
    # 1. Production bounds based on run decision
    for f in factories:
        for t in months:
            # If running, production >= minimum
            model.addConstr(prod[f, t] >= min_prod[f] * run[f, t], 
                           name=f"min_prod_f{f}_t{t}")
            # If running, production <= maximum
            model.addConstr(prod[f, t] <= max_prod[f] * run[f, t], 
                           name=f"max_prod_f{f}_t{t}")
    
    # 2. Demand satisfaction
    for t in months:
        model.addConstr(gp.quicksum(prod[f, t] for f in factories) >= demand[t], 
                       name=f"demand_t{t}")
    
    # Solve
    model.optimize()
    
    # Return results
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
            "status": f"status_{model.status}"
        }