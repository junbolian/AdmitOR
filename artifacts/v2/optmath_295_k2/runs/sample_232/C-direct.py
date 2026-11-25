import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = int(params["num_nodes"])
    nodes = range(n)
    
    # Build cost, capacity, and fixed cost dicts from params
    fixed_cost = {}
    variable_cost = {}
    capacity = {}
    
    for i in nodes:
        for j in nodes:
            if i != j:
                fixed_cost[(i, j)] = params[f"fixed_cost_{i}_{j}"]
                variable_cost[(i, j)] = params[f"variable_cost_{i}_{j}"]
                capacity[(i, j)] = params[f"capacity_{i}_{j}"]
    
    net_outflow = {
        0: params["net_outflow_node0"],
        1: params["net_outflow_node1"],
        2: params["net_outflow_node2"],
        3: params["net_outflow_node3"],
    }
    
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    
    model = gp.Model()
    model.setParam("OutputFlag", 0)
    
    # Binary: whether route (i,j) is established
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")
    # Continuous: flow on route (i,j)
    x = model.addVars(arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="x")
    
    # Objective: minimize fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[arc] * y[arc] + variable_cost[arc] * x[arc] for arc in arcs),
        GRB.MINIMIZE
    )
    
    # Capacity constraints: flow cannot exceed capacity if route is open, 0 otherwise
    for arc in arcs:
        model.addConstr(x[arc] <= capacity[arc] * y[arc], name=f"cap_{arc[0]}_{arc[1]}")
    
    # Flow balance: outflow - inflow = net_outflow for each node
    for i in nodes:
        outflow = gp.quicksum(x[(i, j)] for j in nodes if j != i)
        inflow = gp.quicksum(x[(j, i)] for j in nodes if j != i)
        model.addConstr(outflow - inflow == net_outflow[i], name=f"balance_{i}")
    
    model.optimize()
    
    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}