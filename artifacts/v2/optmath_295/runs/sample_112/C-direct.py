import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distances_list = params["distances"]
    num_selected = params["num_selected"]
    num_nodes = params["num_nodes"]

    # Ordered pairs: (0,1),(0,2),(0,3),(0,4),(1,0),(1,2),(1,3),(1,4),
    #                (2,0),(2,1),(2,3),(2,4),(3,0),(3,1),(3,2),(3,4),
    #                (4,0),(4,1),(4,2),(4,3)
    ordered_pairs = [
        (0,1),(0,2),(0,3),(0,4),
        (1,0),(1,2),(1,3),(1,4),
        (2,0),(2,1),(2,3),(2,4),
        (3,0),(3,1),(3,2),(3,4),
        (4,0),(4,1),(4,2),(4,3)
    ]

    dist = {}
    for idx, (i, j) in enumerate(ordered_pairs):
        dist[(i, j)] = distances_list[idx]

    nodes = list(range(num_nodes))
    all_pairs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if facility i is selected
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # y[i,j] = 1 if both i and j are selected
    y = model.addVars(all_pairs, vtype=GRB.BINARY, name="y")

    # Objective: maximize total pairwise dispersion
    model.setObjective(
        gp.quicksum(dist[(i, j)] * y[i, j] for (i, j) in all_pairs),
        GRB.MAXIMIZE
    )

    # Exactly num_selected facilities selected
    model.addConstr(gp.quicksum(x[i] for i in nodes) == num_selected, name="select_count")

    # Linearization constraints for y[i,j] = x[i] * x[j]
    for (i, j) in all_pairs:
        model.addConstr(y[i, j] <= x[i], name=f"y_xi_{i}_{j}")
        model.addConstr(y[i, j] <= x[j], name=f"y_xj_{i}_{j}")
        model.addConstr(y[i, j] >= x[i] + x[j] - 1, name=f"y_lb_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}