import gurobipy as gp
from gurobipy import GRB

def solve(params):
    factories = [0, 1, 2, 3, 4, 5]
    months = [0, 1, 2, 3]
    
    model = gp.Model("multi_factory_production")
    model.setParam('OutputFlag', 0)
    
    # Decision variables
    # Binary: whether factory f runs in month t
    run = {}
    for f in factories:
        for t in months:
            run[f, t] = model.addVar(vtype=GRB.BINARY, name=f"run_f{f}_m{t}")
    
    # Continuous: production level at factory f in month t
    prod = {}
    for f in factories:
        for t in months:
            prod[f, t] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"prod_f{f}_m{t}")
    
    # Objective: minimize total cost (fixed + variable)
    fixed_cost_total = gp.LinExpr()
    for f in factories:
        for t in months:
            fixed_cost_total += params[f"fixed_cost_f{f}_month{t}"] * run[f, t]
    
    var_cost_total = gp.LinExpr()
    for f in factories:
        for t in months:
            var_cost_total += params[f"var_cost_f{f}"] * prod[f, t]
    
    model.setObjective(fixed_cost_total + var_cost_total, GRB.MINIMIZE)
    
    # Constraints
    # 1. Minimum production if running
    for f in factories:
        for t in months:
            model.addConstr(
                prod[f, t] >= params[f"min_prod_f{f}"] * run[f, t],
                name=f"min_prod_f{f}_m{t}"
            )
    
    # 2. Maximum production if running
    for f in factories:
        for t in months:
            model.addConstr(
                prod[f, t] <= params[f"max_prod_f{f}"] * run[f, t],
                name=f"max_prod_f{f}_m{t}"
            )
    
    # 3. Demand satisfaction
    for t in months:
        total_production = gp.quicksum(prod[f, t] for f in factories)
        model.addConstr(
            total_production >= params[f"demand_month{t}"],
            name=f"demand_m{t}"
        )
    
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