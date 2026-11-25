import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    construction_cost = params["construction_cost"]
    demand = params["demand"]
    bonus = params["bonus"]
    R1 = params["R1"]
    R2 = params["R2"]

    num_nodes = 20
    num_sites = 14

    # Distance matrix: dist[i][j] = distance from node i to site j (0-indexed)
    dist = [
        [7, 50, 103, 64, 66, 55, 25, 92, 10, 48, 48, 47, 78, 36],
        [43, 18, 70, 18, 57, 43, 27, 96, 48, 39, 28, 72, 81, 60],
        [68, 62, 69, 96, 27, 37, 63, 20, 62, 40, 51, 32, 7, 37],
        [18, 38, 84, 63, 43, 33, 19, 70, 14, 27, 31, 30, 55, 17],
        [107, 64, 20, 74, 64, 65, 89, 92, 108, 70, 66, 107, 84, 100],
        [66, 61, 70, 95, 27, 37, 62, 22, 61, 39, 51, 30, 9, 35],
        [58, 20, 39, 49, 25, 17, 41, 65, 58, 21, 17, 60, 51, 52],
        [94, 80, 67, 114, 42, 56, 87, 9, 89, 61, 71, 58, 20, 63],
        [6, 49, 102, 62, 66, 54, 24, 93, 11, 47, 47, 48, 79, 37],
        [48, 27, 52, 61, 13, 3, 35, 51, 46, 8, 17, 41, 36, 33],
        [53, 67, 93, 98, 47, 48, 56, 46, 45, 47, 57, 8, 37, 21],
        [83, 78, 78, 112, 41, 53, 79, 9, 77, 57, 68, 43, 15, 51],
        [54, 10, 48, 34, 39, 27, 35, 80, 56, 27, 17, 67, 65, 57],
        [72, 31, 50, 28, 59, 50, 54, 99, 76, 50, 40, 91, 86, 80],
        [43, 10, 63, 25, 48, 34, 25, 88, 47, 31, 20, 67, 73, 55],
        [30, 16, 72, 34, 47, 33, 12, 85, 34, 27, 19, 57, 69, 44],
        [55, 12, 48, 32, 42, 30, 37, 82, 58, 30, 20, 70, 68, 60],
        [100, 57, 15, 70, 57, 58, 82, 86, 101, 63, 59, 100, 78, 93],
        [28, 17, 69, 44, 38, 24, 11, 74, 29, 17, 14, 46, 59, 34],
        [75, 74, 81, 108, 40, 50, 72, 18, 68, 52, 63, 33, 17, 42],
    ]

    nodes = range(num_nodes)
    sites = range(num_sites)

    # Precompute coverage sets
    # R1_cover[i] = list of sites within R1 of node i
    R1_cover = [[j for j in sites if dist[i][j] <= R1] for i in nodes]
    # R2_cover[i] = list of sites within R2 of node i
    R2_cover = [[j for j in sites if dist[i][j] <= R2] for i in nodes]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[j] = 1 if site j is activated
    x = model.addVars(num_sites, vtype=GRB.BINARY, name="x")
    # y[i] = 1 if node i has ultra-fast charger access (within R2 of some activated site)
    y = model.addVars(num_nodes, vtype=GRB.BINARY, name="y")

    # Objective: minimize total construction cost minus total bonus earned
    model.setObjective(
        gp.quicksum(construction_cost[j] * x[j] for j in sites)
        - gp.quicksum(bonus[i] * y[i] for i in nodes),
        GRB.MINIMIZE
    )

    # Hard constraint: every node must be within R1 of at least one activated site
    for i in nodes:
        if len(R1_cover[i]) == 0:
            # No site can cover this node — infeasible by construction
            return {"objective": None, "status": "infeasible: node cannot be covered"}
        model.addConstr(
            gp.quicksum(x[j] for j in R1_cover[i]) >= 1,
            name=f"coverage_R1_{i}"
        )

    # y[i] can be 1 only if at least one activated site is within R2 of node i
    for i in nodes:
        if len(R2_cover[i]) == 0:
            # No site can give this node ultra-fast access; force y[i] = 0
            model.addConstr(y[i] == 0, name=f"no_ultrafast_{i}")
        else:
            model.addConstr(
                y[i] <= gp.quicksum(x[j] for j in R2_cover[i]),
                name=f"ultrafast_link_{i}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver status {model.Status}"}