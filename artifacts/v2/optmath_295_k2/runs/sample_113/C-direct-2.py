import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    resource_usage = params["resource_usage"]
    capacity = params["capacity"]
    resource_budget = params["resource_budget"]
    
    n_items = 47
    
    try:
        model = gp.Model("production_optimization")
        model.Params.LogToConsole = 0
        
        # Decision variables: quantity to produce for each item
        x = model.addVars(n_items, lb=0, name="x")
        
        # Capacity constraints: production cannot exceed maximum for each item
        for i in range(n_items):
            model.addConstr(x[i] <= capacity[i], name=f"capacity_{i}")
        
        # Resource constraint: total resource usage cannot exceed budget
        model.addConstr(
            gp.quicksum(resource_usage[i] * x[i] for i in range(n_items)) <= resource_budget,
            name="resource_budget"
        )
        
        # Objective: maximize total profit
        model.setObjective(
            gp.quicksum(profit[i] * x[i] for i in range(n_items)),
            GRB.MAXIMIZE
        )
        
        model.optimize()
        
        if model.status == GRB.OPTIMAL:
            return {
                "objective": model.ObjVal,
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
    
    except gp.GurobiError as e:
        return {
            "objective": None,
            "status": f"gurobi_error"
        }