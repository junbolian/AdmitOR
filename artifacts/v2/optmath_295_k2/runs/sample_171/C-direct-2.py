import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]
    
    num_warehouses = 6
    num_stores = 8
    
    try:
        model = gp.Model("supply_chain")
        model.setParam('OutputFlag', 0)
        
        # Decision variables: x[i,j] = units shipped from warehouse i to store j
        x = model.addVars(num_warehouses, num_stores, lb=0, vtype=GRB.CONTINUOUS, name="x")
        
        # Objective: minimize total transportation cost
        model.setObjective(
            gp.quicksum(cost[i][j] * x[i, j] for i in range(num_warehouses) for j in range(num_stores)),
            GRB.MINIMIZE
        )
        
        # Supply constraints: total shipped from each warehouse equals its supply
        for i in range(num_warehouses):
            model.addConstr(
                gp.quicksum(x[i, j] for j in range(num_stores)) == supply[i],
                name=f"supply_{i}"
            )
        
        # Demand constraints: total received by each store equals its demand
        for j in range(num_stores):
            model.addConstr(
                gp.quicksum(x[i, j] for i in range(num_warehouses)) == demand[j],
                name=f"demand_{j}"
            )
        
        # Capacity constraints: shipment cannot exceed capacity
        for i in range(num_warehouses):
            for j in range(num_stores):
                model.addConstr(x[i, j] <= capacity[i][j], name=f"capacity_{i}_{j}")
        
        # Solve the model
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
        elif model.status == GRB.UNBOUNDED:
            return {
                "objective": None,
                "status": "unbounded"
            }
        else:
            return {
                "objective": None,
                "status": "failed"
            }
    
    except gp.GurobiError as e:
        return {
            "objective": None,
            "status": f"gurobi_error"
        }