import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_select = params["num_facilities_to_select"]
    M = params["large_constant_M"]

    nodes = [0, 1, 2, 3, 4]
    pairs = [(i, j) for i in nodes for j in nodes if i < j]

    dist = {
        (0, 1): params["distance_01"],
        (0, 2): params["distance_02"],
        (0, 3): params["distance_03"],
        (0, 4): params["distance_04"],
        (1, 2): params["distance_12"],
        (1, 3): params["distance_13"],
        (1, 4): params["distance_14"],
        (2, 3): params["distance_23"],
        (2, 4): params["distance_24"],
        (3, 4): params["distance_34"],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: node i is selected
    x = {i: model.addVar(vtype=GRB.BINARY, name=f"x_{i}") for i in nodes}

    # Binary variable: both nodes i and j are selected
    y = {(i, j): model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}") for (i, j) in pairs}

    # Continuous variable: minimum distance
    z = model.addVar(lb=0.0, name="z")

    # Objective: maximize minimum distance
    model.setObjective(z, GRB.MAXIMIZE)

    # Select exactly num_select facilities
    model.addConstr(gp.quicksum(x[i] for i in nodes) == num_select, name="select_count")

    for (i, j) in pairs:
        d_ij = dist[(i, j)]

        # z <= d_ij + M * (1 - y[i,j])
        # i.e., z + M * y[i,j] <= d_ij + M
        model.addConstr(z + M * y[(i, j)] <= d_ij + M, name=f"min_dist_{i}_{j}")

        # y[i,j] <= x[i]
        model.addConstr(y[(i, j)] <= x[i], name=f"y_leq_xi_{i}_{j}")

        # y[i,j] <= x[j]
        model.addConstr(y[(i, j)] <= x[j], name=f"y_leq_xj_{i}_{j}")

        # y[i,j] >= x[i] + x[j] - 1
        model.addConstr(y[(i, j)] >= x[i] + x[j] - 1, name=f"y_geq_sum_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}