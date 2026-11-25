import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]
    
    num_producers = 3
    num_contracts = 4
    
    try:
        model = gp.Model("energy_allocation")
        model.Params.OutputFlag = 0
        
        # Decision variables: energy allocated from producer i to contract j
        x = {}
        for i in range(num_producers):
            for j in range(num_contracts):
                x[i, j] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"x_{i}_{j}")
        
        # Binary variables: whether producer i participates in contract j
        y = {}
        for i in range(num_producers):
            for j in range(num_contracts):
                y[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")
        
        # Objective: minimize total production cost
        obj = gp.quicksum(cost[i][j] * x[i, j] for i in range(num_producers) for j in range(num_contracts))
        model.setObjective(obj, GRB.MINIMIZE)
        
        # Constraint: each producer cannot exceed their capacity
        for i in range(num_producers):
            model.addConstr(
                gp.quicksum(x[i, j] for j in range(num_contracts)) <= capacity[i],
                name=f"capacity_{i}"
            )
        
        # Constraint: each contract must meet its demand
        for j in range(num_contracts):
            model.addConstr(
                gp.quicksum(x[i, j] for i in range(num_producers)) >= demand[j],
                name=f"demand_{j}"
            )
        
        # Constraint: each contract must have at least 2 producers
        for j in range(num_contracts):
            model.addConstr(
                gp.quicksum(y[i, j] for i in range(num_producers)) >= 2,
                name=f"min_contributors_{j}"
            )
        
        # Constraint: if producer participates in contract, must meet minimum delivery
        # x[i,j] >= min_delivery[i] * y[i,j]
        # x[i,j] <= capacity[i] * y[i,j]
        for i in range(num_producers):
            for j in range(num_contracts):
                model.addConstr(
                    x[i, j] >= min_delivery[i] * y[i, j],
                    name=f"min_delivery_{i}_{j}"
                )
                model.addConstr(
                    x[i, j] <= capacity[i] * y[i, j],
                    name=f"participation_{i}_{j}"
                )
        
        model.optimize()
        
        if model.Status == GRB.OPTIMAL:
            return {
                "objective": model.ObjVal,
                "status": "optimal"
            }
        elif model.Status == GRB.INFEASIBLE:
            return {
                "objective": None,
                "status": "infeasible"
            }
        elif model.Status == GRB.UNBOUNDED:
            return {
                "objective": None,
                "status": "unbounded"
            }
        else:
            return {
                "objective": None,
                "status": f"status_{model.Status}"
            }
    
    except gp.GurobiError as e:
        return {
            "objective": None,
            "status": f"gurobi_error"
        }