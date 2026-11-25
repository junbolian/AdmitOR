import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    costs = params["costs"]
    supplies = params["supplies"]
    # coordinates present in params but not needed for the optimization model
    # coordinates = params["coordinates"]

    arcs = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2),
        (2, 3), (2, 7),
        (3, 4),
        (4, 5), (4, 7), (4, 8),
        (5, 6), (5, 9),
        (6, 7), (6, 8),
        (7, 8),
        (8, 9),
    ]

    num_nodes = 10

    model = gp.Model("emergency_routing")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow on each arc
    flow = {}
    for idx, (i, j) in enumerate(arcs):
        flow[(i, j)] = model.addVar(
            lb=0,
            ub=capacities[idx],
            obj=costs[idx],
            vtype=GRB.CONTINUOUS,
            name=f"flow_{i}_{j}"
        )

    model.ModelSense = GRB.MINIMIZE

    # Flow conservation constraints
    for node in range(num_nodes):
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in arcs if i == node)
        inflow  = gp.quicksum(flow[(i, j)] for (i, j) in arcs if j == node)
        model.addConstr(outflow - inflow == supplies[node], name=f"balance_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}