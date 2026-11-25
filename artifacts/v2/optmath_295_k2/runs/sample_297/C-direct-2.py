import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_facilities = params["num_facilities"]
    big_M = params["big_M"]

    distances = {
        (0, 1): params["distance_0_1"],
        (0, 2): params["distance_0_2"],
        (0, 3): params["distance_0_3"],
        (1, 0): params["distance_1_0"],
        (1, 2): params["distance_1_2"],
        (1, 3): params["distance_1_3"],
        (2, 0): params["distance_2_0"],
        (2, 1): params["distance_2_1"],
        (2, 3): params["distance_2_3"],
        (3, 0): params["distance_3_0"],
        (3, 1): params["distance_3_1"],
        (3, 2): params["distance_3_2"],
    }

    nodes = [0, 1, 2, 3]
    pairs = list(distances.keys())

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    node_vars = model.addVars(nodes, vtype=GRB.BINARY, name="Nodes")
    pair_vars = model.addVars(pairs, vtype=GRB.BINARY, name="PairSelection")
    min_dist = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="MinDistance")

    model.setObjective(min_dist, GRB.MAXIMIZE)

    model.addConstr(gp.quicksum(node_vars[n] for n in nodes) == num_facilities, name="total_facilities")

    for (i, j), dist in distances.items():
        model.addConstr(
            min_dist <= dist + big_M * (1 - pair_vars[i, j]),
            name=f"dist_constr_{i}_{j}"
        )

    for (i, j) in pairs:
        model.addConstr(pair_vars[i, j] <= node_vars[i], name=f"pair_le_i_{i}_{j}")
        model.addConstr(pair_vars[i, j] <= node_vars[j], name=f"pair_le_j_{i}_{j}")
        model.addConstr(pair_vars[i, j] >= node_vars[i] + node_vars[j] - 1, name=f"pair_ge_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}