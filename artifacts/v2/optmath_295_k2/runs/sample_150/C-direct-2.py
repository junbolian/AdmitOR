import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 6
    # All directed edges (no self-loops)
    edges = [(i, j) for i in range(n) for j in range(n) if i != j]

    # Build cost/capacity dicts from params
    fixed_cost = {}
    variable_cost = {}
    capacity = {}
    for (i, j) in edges:
        fixed_cost[(i, j)]    = params[f"fixed_cost_{i}_{j}"]
        variable_cost[(i, j)] = params[f"variable_cost_{i}_{j}"]
        capacity[(i, j)]      = params[f"capacity_{i}_{j}"]

    supply_demand = params["supply_demand"]  # list of length 6

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: establish connection (i,j)
    y = model.addVars(edges, vtype=GRB.BINARY, name="y")
    # Continuous: flow on (i,j)
    x = model.addVars(edges, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[e] * y[e] + variable_cost[e] * x[e] for e in edges),
        GRB.MINIMIZE
    )

    # Flow balance: outflow - inflow = supply_demand[i]
    for i in range(n):
        out_flow = gp.quicksum(x[(i, j)] for j in range(n) if i != j)
        in_flow  = gp.quicksum(x[(j, i)] for j in range(n) if i != j)
        model.addConstr(out_flow - in_flow == supply_demand[i], name=f"balance_{i}")

    # Capacity and linking constraints
    for e in edges:
        model.addConstr(x[e] <= capacity[e] * y[e], name=f"cap_{e[0]}_{e[1]}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}