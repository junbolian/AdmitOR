import gurobipy as gp
from gurobipy import GRB

def solve(params):
    bandwidth_demand = params["bandwidth_demand"]

    n_nodes = 8
    # Upper bound on FSU index: sum of all demands is a safe upper bound
    M = sum(bandwidth_demand)

    edges = [(0,1),(2,4),(2,7),(3,7),(1,4),(2,3),(0,5),(2,5),(3,5)]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # s[i] = starting FSU index for node i (0-based)
    s = model.addVars(n_nodes, vtype=GRB.INTEGER, lb=0, ub=M, name="s")

    # max_fsu = maximum ending FSU index across all nodes
    max_fsu = model.addVar(vtype=GRB.INTEGER, lb=0, ub=M, name="max_fsu")

    # Objective: minimize the maximum ending slot
    model.setObjective(max_fsu, GRB.MINIMIZE)

    # max_fsu >= s[i] + d[i] for all i
    for i in range(n_nodes):
        model.addConstr(max_fsu >= s[i] + bandwidth_demand[i], name=f"span_{i}")

    # Non-overlap constraints for each edge (i, j):
    # Either s[i] + d[i] <= s[j]  OR  s[j] + d[j] <= s[i]
    # Introduce binary variable y[e]: y=1 means i is below j, y=0 means j is below i
    y = {}
    for idx, (i, j) in enumerate(edges):
        y[idx] = model.addVar(vtype=GRB.BINARY, name=f"y_{idx}")
        di = bandwidth_demand[i]
        dj = bandwidth_demand[j]
        # If y=1: s[i] + di <= s[j]
        model.addConstr(s[i] + di <= s[j] + M * (1 - y[idx]), name=f"no_overlap_ij_{idx}")
        # If y=0: s[j] + dj <= s[i]
        model.addConstr(s[j] + dj <= s[i] + M * y[idx], name=f"no_overlap_ji_{idx}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}