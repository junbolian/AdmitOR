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

    # Precompute pairwise distances
    pairs = [(nodes[i], nodes[j]) for i in range(len(nodes)) for j in range(i+1, len(nodes))]
    dist = {}
    for (u, v) in pairs:
        xu, yu = coords[u]
        xv, yv = coords[v]
        dist[(u, v)] = math.sqrt((xu - xv)**2 + (yu - yv)**2)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: is node selected?
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Binary variable: are both nodes in a pair selected?
    z = model.addVars(pairs, vtype=GRB.BINARY, name="z")

    # Continuous variable: minimum distance
    min_dist = model.addVar(lb=0.0, name="MinDistance")

    # Objective: maximize minimum distance
    model.setObjective(min_dist, GRB.MAXIMIZE)

    # Constraint: select exactly num_selected facilities
    model.addConstr(gp.quicksum(x[n] for n in nodes) == num_selected, name="select_count")

    # Pairwise constraints
    for (u, v) in pairs:
        d = dist[(u, v)]

        # MinDistance <= dist(u,v) + big_M*(1 - z[u,v])
        model.addConstr(min_dist <= d + big_M * (1 - z[u, v]), name=f"min_dist_{u}_{v}")

        # z[u,v] consistency: z <= x[u], z <= x[v], z >= x[u] + x[v] - 1
        model.addConstr(z[u, v] <= x[u], name=f"z_le_xu_{u}_{v}")
        model.addConstr(z[u, v] <= x[v], name=f"z_le_xv_{u}_{v}")
        model.addConstr(z[u, v] >= x[u] + x[v] - 1, name=f"z_ge_sum_{u}_{v}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}