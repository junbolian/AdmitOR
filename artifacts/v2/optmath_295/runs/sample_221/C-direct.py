import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 8
    nodes = list(range(n))
    
    # Build edge list and cost dict from params
    edges = [(i, j) for i in nodes for j in nodes if i != j]
    cost = {(i, j): params[f"edge_cost_{i}_{j}"] for (i, j) in edges}
    
    model = gp.Model("shortest_path")
    model.setParam("OutputFlag", 0)
    
    # Binary flow variables
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")
    
    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[e] * x[e] for e in edges), GRB.MINIMIZE)
    
    # Flow balance constraints
    net_supply_0 = params["net_supply_node_0"]
    net_demand_7 = params["net_demand_node_7"]
    flow_balance_intermediate = params["flow_balance_intermediate"]
    
    for node in nodes:
        outflow = gp.quicksum(x[node, j] for j in nodes if j != node)
        inflow = gp.quicksum(x[i, node] for i in nodes if i != node)
        
        if node == 0:
            # net outflow = net_supply_node_0
            model.addConstr(outflow - inflow == net_supply_0, name=f"balance_{node}")
        elif node == 7:
            # net inflow = net_demand_node_7
            model.addConstr(inflow - outflow == net_demand_7, name=f"balance_{node}")
        else:
            # intermediate: inflow - outflow = flow_balance_intermediate (should be 0)
            model.addConstr(inflow - outflow == flow_balance_intermediate, name=f"balance_{node}")
    
    model.optimize()
    
    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}