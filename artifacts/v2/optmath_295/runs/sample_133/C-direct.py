import gurobipy as gp
from gurobipy import GRB

def solve(params):
    p = params["p"]
    n_nodes = params["n_nodes"]
    big_M = params["big_M"]

    # Build distance dict for all pairs
    dist = {}
    dist[(0,1)] = params["dist_0_1"]
    dist[(0,2)] = params["dist_0_2"]
    dist[(0,3)] = params["dist_0_3"]
    dist[(0,4)] = params["dist_0_4"]
    dist[(1,2)] = params["dist_1_2"]
    dist[(1,3)] = params["dist_1_3"]
    dist[(1,4)] = params["dist_1_4"]
    dist[(2,3)] = params["dist_2_3"]
    dist[(2,4)] = params["dist_2_4"]
    dist[(3,4)] = params["dist_3_4"]

    nodes = list(range(n_nodes))
    pairs = [(i, j) for i in nodes for j in nodes if i < j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: node i is selected
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Binary variable: both nodes i and j are selected
    y = model.addVars(pairs, vtype=GRB.BINARY, name="y")

    # Continuous variable: minimum distance between any two selected facilities
    d_min = model.addVar(lb=0.0, name="d_min")

    # Objective: maximize minimum distance
    model.setObjective(d_min, GRB.MAXIMIZE)

    # Exactly p facilities selected
    model.addConstr(gp.quicksum(x[i] for i in nodes) == p, name="select_p")

    for (i, j) in pairs:
        d_ij = dist[(i, j)]

        # If y[i,j] == 1 (both selected), enforce d_min <= d_ij
        # Constraint: d_min + big_M * y[i,j] <= d_ij + big_M
        # Rearranged: d_min <= d_ij + big_M * (1 - y[i,j])
        model.addConstr(d_min <= d_ij + big_M * (1 - y[i, j]),
                        name=f"dist_{i}_{j}")

        # Pairwise linking constraints
        # y[i,j] <= x[i]
        model.addConstr(y[i, j] <= x[i], name=f"link_{i}_{j}_i")
        # y[i,j] <= x[j]
        model.addConstr(y[i, j] <= x[j], name=f"link_{i}_{j}_j")
        # y[i,j] >= x[i] + x[j] - 1
        model.addConstr(y[i, j] >= x[i] + x[j] - 1, name=f"link_{i}_{j}_both")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}