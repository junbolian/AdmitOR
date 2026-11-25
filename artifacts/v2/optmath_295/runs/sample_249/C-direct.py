import gurobipy as gp
from gurobipy import GRB


def solve(params):
    transport_cost = params["transport_cost"]
    joint_capacity = params["joint_capacity"]

    # Build per-product capacity lookup: cap[p][i][j]
    cap = {0: {}, 1: {}}
    for i in range(4):
        cap[0][i] = {}
        cap[1][i] = {}
        for j in range(4):
            if i == j:
                continue
            key0 = f"product0_capacity_{i}{j}"
            key1 = f"product1_capacity_{i}{j}"
            cap[0][i][j] = params[key0]
            cap[1][i][j] = params[key1]

    # Net flow requirements: net_flow[city][product]
    net_flow = {}
    for i in range(4):
        net_flow[i] = {}
        for p in range(2):
            net_flow[i][p] = params[f"net_flow_{i}_product{p}"]

    cities = range(4)
    products = range(2)
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[p][i][j] = units of product p shipped from city i to city j
    x = {}
    for p in products:
        for i, j in arcs:
            x[p, i, j] = model.addVar(lb=0.0, name=f"x_{p}_{i}_{j}")

    # Objective: minimize total transport cost
    model.setObjective(
        transport_cost * gp.quicksum(x[p, i, j] for p in products for i, j in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints
    for i in cities:
        for p in products:
            outflow = gp.quicksum(x[p, i, j] for j in cities if j != i)
            inflow = gp.quicksum(x[p, j, i] for j in cities if j != i)
            model.addConstr(outflow - inflow == net_flow[i][p], name=f"flow_{i}_{p}")

    # Joint capacity constraints
    for i, j in arcs:
        model.addConstr(
            gp.quicksum(x[p, i, j] for p in products) <= joint_capacity,
            name=f"joint_{i}_{j}"
        )

    # Product-specific capacity constraints
    for p in products:
        for i, j in arcs:
            model.addConstr(x[p, i, j] <= cap[p][i][j], name=f"cap_{p}_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}