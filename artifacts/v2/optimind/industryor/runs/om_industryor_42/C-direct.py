import gurobipy as gp
from gurobipy import GRB

def solve(params):
    a1 = params["a1"]
    a2 = params["a2"]
    b1 = params["b1"]
    b2 = params["b2"]
    f1 = params["f1"]
    f2 = params["f2"]
    q1 = params["q1"]
    q2 = params["q2"]
    c11 = params["c11"]
    c12 = params["c12"]
    c21 = params["c21"]
    c22 = params["c22"]
    c11p = params["c11p"]
    c12p = params["c12p"]
    c21p = params["c21p"]
    c22p = params["c22p"]

    a = [a1, a2]
    b = [b1, b2]
    f = [f1, f2]
    q = [q1, q2]
    c = [[c11, c12], [c21, c22]]
    cp = [[c11p, c12p], [c21p, c22p]]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][k]: flow from production i to station k
    x = [[model.addVar(lb=0, name=f"x_{i}_{k}") for k in range(2)] for i in range(2)]
    # y[k][j]: flow from station k to demand j
    y = [[model.addVar(lb=0, name=f"y_{k}_{j}") for j in range(2)] for k in range(2)]
    # z[k]: binary, 1 if station k is used
    z = [model.addVar(vtype=GRB.BINARY, name=f"z_{k}") for k in range(2)]

    # Objective: fixed costs + transport costs
    obj = gp.quicksum(f[k] * z[k] for k in range(2))
    obj += gp.quicksum(c[i][k] * x[i][k] for i in range(2) for k in range(2))
    obj += gp.quicksum(cp[k][j] * y[k][j] for k in range(2) for j in range(2))
    model.setObjective(obj, GRB.MINIMIZE)

    # Supply constraints: total shipped from production i <= a[i]
    for i in range(2):
        model.addConstr(gp.quicksum(x[i][k] for k in range(2)) <= a[i], name=f"supply_{i}")

    # Demand constraints: total received at demand j >= b[j]
    for j in range(2):
        model.addConstr(gp.quicksum(y[k][j] for k in range(2)) >= b[j], name=f"demand_{j}")

    # Flow balance at each station: inflow = outflow
    for k in range(2):
        model.addConstr(
            gp.quicksum(x[i][k] for i in range(2)) == gp.quicksum(y[k][j] for j in range(2)),
            name=f"balance_{k}"
        )

    # Capacity constraints: total through station k <= q[k] * z[k]
    for k in range(2):
        model.addConstr(
            gp.quicksum(x[i][k] for i in range(2)) <= q[k] * z[k],
            name=f"capacity_{k}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}