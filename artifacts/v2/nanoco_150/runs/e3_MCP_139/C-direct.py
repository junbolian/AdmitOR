import gurobipy as gp
from gurobipy import GRB

def solve(params):
    bandwidth = params["bandwidth"]
    
    n_towers = 8
    towers = list(range(n_towers))
    
    edges = [(0,1),(2,4),(2,7),(3,7),(1,4),(2,3),(0,5),(2,5),(3,5)]
    
    total_bw = sum(bandwidth[i] for i in towers)
    # Upper bound on spectrum: sum of all bandwidths
    M = total_bw
    
    model = gp.Model("frequency_band_planning")
    model.setParam("OutputFlag", 0)
    
    # start[i] = starting frequency of tower i (integer)
    start = model.addVars(towers, lb=0, ub=M, vtype=GRB.INTEGER, name="start")
    
    # Objective: minimize the maximum ending frequency
    max_end = model.addVar(lb=0, ub=M, vtype=GRB.INTEGER, name="max_end")
    
    model.setObjective(max_end, GRB.MINIMIZE)
    
    # max_end >= start[i] + bandwidth[i] for all i
    for i in towers:
        model.addConstr(max_end >= start[i] + bandwidth[i], name=f"max_end_{i}")
    
    # Non-overlap constraints for each interfering pair
    # For edge (i, j): either start[i] + bandwidth[i] <= start[j]
    #                  or start[j] + bandwidth[j] <= start[i]
    # Introduce binary variable y[i,j] = 1 if i is entirely before j
    y = {}
    for (i, j) in edges:
        y[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")
        # If y=1: start[i] + bw[i] <= start[j]
        model.addConstr(
            start[i] + bandwidth[i] <= start[j] + M * (1 - y[i, j]),
            name=f"no_overlap_ij_{i}_{j}"
        )
        # If y=0: start[j] + bw[j] <= start[i]
        model.addConstr(
            start[j] + bandwidth[j] <= start[i] + M * y[i, j],
            name=f"no_overlap_ji_{i}_{j}"
        )
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}