import gurobipy as gp
from gurobipy import GRB

def solve(params):
    nodes = range(6)
    # All directed edges (no self-loops)
    edges = [(i, j) for i in nodes for j in nodes if i != j]

    # Build cost/capacity dicts from params
    fixed_cost = {(i, j): params[f"fixed_cost_{i}_{j}"] for i, j in edges}
    var_cost   = {(i, j): params[f"variable_cost_{i}_{j}"] for i, j in edges}
    capacity   = {(i, j): params[f"capacity_{i}_{j}"] for i, j in edges}
    supply     = {i: params["supply_demand"][i] for i in nodes}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[i,j] = 1 if connection i->j is established
    y = model.addVars(edges, vtype=GRB.BINARY, name="y")
    # x[i,j] = flow on connection i->j
    x = model.addVars(edges, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: fixed costs + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[e] * y[e] + var_cost[e] * x[e] for e in edges),
        GRB.MINIMIZE
    )

    # Capacity constraints: flow <= capacity * y
    for e in edges:
        model.addConstr(x[e] <= capacity[e] * y[e], name=f"cap_{e[0]}_{e[1]}")

    # Flow balance: outflow - inflow = supply (positive) or demand (negative)
    for i in nodes:
        out_flow = gp.quicksum(x[i, j] for j in nodes if j != i)
        in_flow  = gp.quicksum(x[j, i] for j in nodes if j != i)
        model.addConstr(out_flow - in_flow == supply[i], name=f"balance_{i}")

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