import gurobipy as gp
from gurobipy import GRB

def solve(params):
    net_demand = params["net_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    nodes = [0, 1, 2, 3]
    arcs = [(0,1),(0,2),(0,3),(1,0),(1,2),(1,3),(2,0),(2,1),(2,3),(3,0),(3,1),(3,2)]

    fc = {arc: fixed_cost[i] for i, arc in enumerate(arcs)}
    vc = {arc: variable_cost[i] for i, arc in enumerate(arcs)}
    cap = {arc: capacity[i] for i, arc in enumerate(arcs)}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: establish connection
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")
    # Continuous: flow on each arc
    x = model.addVars(arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: minimize fixed + variable costs
    model.setObjective(
        gp.quicksum(fc[a] * y[a] + vc[a] * x[a] for a in arcs),
        GRB.MINIMIZE
    )

    # Capacity and linking constraints
    for a in arcs:
        model.addConstr(x[a] <= cap[a] * y[a], name=f"cap_{a[0]}_{a[1]}")

    # Flow balance: inflow - outflow = net_demand
    for nd in nodes:
        inflow = gp.quicksum(x[(i, nd)] for (i, j) in arcs if j == nd)
        outflow = gp.quicksum(x[(nd, j)] for (i, j) in arcs if i == nd)
        model.addConstr(inflow - outflow == net_demand[nd], name=f"balance_{nd}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}