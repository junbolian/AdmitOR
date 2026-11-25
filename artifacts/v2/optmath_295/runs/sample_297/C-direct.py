import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_nodes = params["num_nodes"]
    num_selected = params["num_selected"]
    bigM = params["bigM"]

    # Read all directed distances from params
    dist = {}
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                dist[(i, j)] = params[f"dist_{i}_{j}"]

    model = gp.Model("facility_dispersion")
    model.Params.OutputFlag = 0

    # Binary: whether node i is selected as a facility
    nodes = model.addVars(num_nodes, vtype=GRB.BINARY, name="nodes")

    # Binary: whether both nodes i and j are selected (for each ordered pair)
    pair_sel = {}
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                pair_sel[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"pair_{i}_{j}")

    # Continuous: the minimum distance among selected pairs (objective variable)
    min_dist = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="min_dist")

    # Constraint 1: exactly num_selected facilities chosen
    model.addConstr(
        gp.quicksum(nodes[i] for i in range(num_nodes)) == num_selected,
        name="total_selected",
    )

    # Constraint 2 & 3: pair-selection logic + distance deactivation
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                # PairSelection[i,j] <= Nodes[i]
                model.addConstr(pair_sel[(i, j)] <= nodes[i], name=f"pair_le_i_{i}_{j}")
                # PairSelection[i,j] <= Nodes[j]
                model.addConstr(pair_sel[(i, j)] <= nodes[j], name=f"pair_le_j_{i}_{j}")
                # PairSelection[i,j] >= Nodes[i] + Nodes[j] - 1
                model.addConstr(
                    pair_sel[(i, j)] >= nodes[i] + nodes[j] - 1,
                    name=f"pair_ge_{i}_{j}",
                )
                # MinDistance <= dist[i,j] + bigM*(1 - PairSelection[i,j])
                model.addConstr(
                    min_dist <= dist[(i, j)] + bigM * (1 - pair_sel[(i, j)]),
                    name=f"dist_con_{i}_{j}",
                )

    model.setObjective(min_dist, GRB.MAXIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}