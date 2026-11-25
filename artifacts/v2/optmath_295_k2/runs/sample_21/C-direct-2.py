import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pairwise_distances = params["pairwise_distances"]
    num_to_open = params["num_facilities_to_open"]

    n = 5
    nodes = range(n)

    # Build distance dict from list of values ordered as (0,1),(0,2),...
    pairs_order = [(i, j) for i in nodes for j in nodes if i != j]
    dist = {}
    for idx, (i, j) in enumerate(pairs_order):
        dist[(i, j)] = pairwise_distances[idx]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: facility i is opened
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Binary: both facility i and j are opened (directed pairs)
    y = model.addVars(
        [(i, j) for i in nodes for j in nodes if i != j],
        vtype=GRB.BINARY,
        name="y"
    )

    # Objective: maximize total pairwise dispersion
    model.setObjective(
        gp.quicksum(dist[(i, j)] * y[(i, j)] for i in nodes for j in nodes if i != j),
        GRB.MAXIMIZE
    )

    # Exactly num_to_open facilities opened
    model.addConstr(gp.quicksum(x[i] for i in nodes) == num_to_open, name="total_open")

    # Pairwise linking constraints
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            # y[i,j] can be 1 only if both x[i] and x[j] are 1
            model.addConstr(y[(i, j)] <= x[i], name=f"link_i_{i}_{j}")
            model.addConstr(y[(i, j)] <= x[j], name=f"link_j_{i}_{j}")
            model.addConstr(y[(i, j)] >= x[i] + x[j] - 1, name=f"link_both_{i}_{j}")

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