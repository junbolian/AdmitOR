import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    min_distance_lower_bound = params["min_distance_lower_bound"]
    min_distance_upper_bound = params["min_distance_upper_bound"]
    big_M = params["big_M"]
    exact_selection_count = params["exact_selection_count"]
    num_nodes = params["num_nodes"]

    # Fixed node positions for 5 nodes (structural constants)
    positions = {
        0: (0, 0),
        1: (1, 0),
        2: (0, 1),
        3: (1, 1),
        4: (0.5, 0.5),
    }

    nodes = list(range(num_nodes))
    pairs = [(i, j) for i in nodes for j in nodes if i < j]

    # Precompute distances
    dist = {}
    for (i, j) in pairs:
        xi, yi = positions[i]
        xj, yj = positions[j]
        dist[(i, j)] = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary selection variables
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Pairwise selection variables: 1 if both i and j are selected
    z = model.addVars(pairs, vtype=GRB.BINARY, name="z")

    # Minimum distance variable
    min_dist = model.addVar(
        lb=min_distance_lower_bound,
        ub=min_distance_upper_bound,
        vtype=GRB.CONTINUOUS,
        name="MinDistance"
    )

    # Objective: maximize minimum distance
    model.setObjective(min_dist, GRB.MAXIMIZE)

    # Exactly k facilities selected
    model.addConstr(gp.quicksum(x[i] for i in nodes) == exact_selection_count, name="select_count")

    for (i, j) in pairs:
        # min_dist <= dist[i,j] + big_M * (1 - z[i,j])
        model.addConstr(
            min_dist <= dist[(i, j)] + big_M * (1 - z[(i, j)]),
            name=f"dist_relax_{i}_{j}"
        )

        # z[i,j] <= x[i]
        model.addConstr(z[(i, j)] <= x[i], name=f"z_xi_{i}_{j}")
        # z[i,j] <= x[j]
        model.addConstr(z[(i, j)] <= x[j], name=f"z_xj_{i}_{j}")
        # z[i,j] >= x[i] + x[j] - 1
        model.addConstr(z[(i, j)] >= x[i] + x[j] - 1, name=f"z_both_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}