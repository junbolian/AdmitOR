import gurobipy as gp
from gurobipy import GRB

def solve(params):
    d01 = params["d01"]
    d02 = params["d02"]
    d03 = params["d03"]
    d10 = params["d10"]
    d12 = params["d12"]
    d13 = params["d13"]
    d20 = params["d20"]
    d21 = params["d21"]
    d23 = params["d23"]
    d30 = params["d30"]
    d31 = params["d31"]
    d32 = params["d32"]

    n_nodes = 4
    nodes = range(n_nodes)

    # Build dispersion dict for all ordered pairs (i,j) with i != j
    disp = {
        (0,1): d01, (0,2): d02, (0,3): d03,
        (1,0): d10, (1,2): d12, (1,3): d13,
        (2,0): d20, (2,1): d21, (2,3): d23,
        (3,0): d30, (3,1): d31, (3,2): d32
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variables: x[i] = 1 if node i is selected
    x = model.addVars(n_nodes, vtype=GRB.BINARY, name="x")

    # Binary variables: y[i,j] = 1 if both node i and node j are selected
    pairs = [(i, j) for i in nodes for j in nodes if i != j]
    y = model.addVars(pairs, vtype=GRB.BINARY, name="y")

    # Objective: maximize total dispersion over all ordered pairs
    model.setObjective(
        gp.quicksum(disp[i, j] * y[i, j] for (i, j) in pairs),
        GRB.MAXIMIZE
    )

    # Exactly 3 facilities selected
    model.addConstr(gp.quicksum(x[i] for i in nodes) == 3, name="select_3")

    # Pairwise activation constraints: y[i,j] = 1 only if both x[i] and x[j] = 1
    for (i, j) in pairs:
        model.addConstr(y[i, j] <= x[i], name=f"y_xi_{i}_{j}")
        model.addConstr(y[i, j] <= x[j], name=f"y_xj_{i}_{j}")
        model.addConstr(y[i, j] >= x[i] + x[j] - 1, name=f"y_lb_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}