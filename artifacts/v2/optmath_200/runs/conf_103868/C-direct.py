import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 8
    nodes = list(range(n))
    
    # Build cost dict from params
    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]
    
    net_supply = params["net_supply_node_0"]
    net_demand = params["net_demand_node_7"]
    
    model = gp.Model()
    model.setParam("OutputFlag", 0)
    
    # Binary decision variables x[i,j] = 1 if route i->j is used
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
    
    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )
    
    # Flow balance constraints
    for node in nodes:
        outflow = gp.quicksum(x[(node, j)] for j in nodes if j != node)
        inflow = gp.quicksum(x[(i, node)] for i in nodes if i != node)
        
        if node == 0:
            # net outflow = net_supply
            model.addConstr(outflow - inflow == net_supply, name=f"balance_{node}")
        elif node == 7:
            # net inflow = net_demand
            model.addConstr(inflow - outflow == net_demand, name=f"balance_{node}")
        else:
            # flow conservation
            model.addConstr(inflow - outflow == 0, name=f"balance_{node}")
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}