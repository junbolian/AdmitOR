import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    num_selected = params["num_facilities_selected"]
    big_M = params["big_M"]

    # Fixed node coordinates (5 nodes)
    nodes = ["node_0", "node_1", "node_2", "node_3", "node_4"]
    coords = {
        "node_0": (0, 0),
        "node_1": (1, 0),
        "node_2": (0, 1),
        "node_3": (1, 1),
        "node_4": (0.5, 0.5),
    }

    # Precompute distances between all pairs
    pairs = [(nodes[i], nodes[j]) for i in range(len(nodes)) for j in range(i+1, len(nodes))]
    dist = {}
    for (u, v) in pairs:
        xu, yu = coords[u]
        xv, yv = coords[v]
        dist[(u, v)] = math.sqrt((xu - xv)**2 + (yu - yv)**2)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: select node
    x = {n: model.addVar(vtype=GRB.BINARY, name=f"x_{n}") for n in nodes}

    # Binary variable: pairwise selection (1 if both selected)
    z = {(u, v): model.addVar(vtype=GRB.BINARY, name=f"z_{u}_{v}") for (u, v) in pairs}

    # Continuous variable: minimum distance
    min_dist = model.addVar(lb=0.0, name="MinDistance")

    # Objective: maximize minimum distance
    model.setObjective(min_dist, GRB.MAXIMIZE)

    # Exactly num_selected nodes selected
    model.addConstr(gp.quicksum(x[n] for n in nodes) == num_selected, name="select_count")

    for (u, v) in pairs:
        d = dist[(u, v)]

        # MinDistance <= dist(u,v) if both selected, relaxed otherwise
        # min_dist <= d + big_M * (1 - z[u,v])
        model.addConstr(min_dist <= d + big_M * (1 - z[(u, v)]), name=f"md_{u}_{v}")

        # Pairwise consistency: z <= x_u, z <= x_v, z >= x_u + x_v - 1
        model.addConstr(z[(u, v)] <= x[u], name=f"z_u_{u}_{v}")
        model.addConstr(z[(u, v)] <= x[v], name=f"z_v_{u}_{v}")
        model.addConstr(z[(u, v)] >= x[u] + x[v] - 1, name=f"z_lb_{u}_{v}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}