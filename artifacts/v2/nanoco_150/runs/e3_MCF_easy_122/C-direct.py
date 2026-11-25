import gurobipy as gp
from gurobipy import GRB

def solve(params):
    routes = [
        (0, 2), (0, 3),
        (1, 2), (1, 3),
        (2, 4), (2, 5),
        (3, 4), (3, 5),
        (0, 4), (0, 5),
        (1, 4), (1, 5),
    ]

    supply = {
        0: params["supply_0"],
        1: params["supply_1"],
        2: params["supply_2"],
        3: params["supply_3"],
        4: params["supply_4"],
        5: params["supply_5"],
    }

    capacity = {
        (i, j): params[f"capacity_{i}_{j}"] for (i, j) in routes
    }

    cost = {
        (i, j): params[f"cost_{i}_{j}"] for (i, j) in routes
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    flow = model.addVars(routes, lb=0.0, name="flow")

    for (i, j) in routes:
        model.addConstr(flow[i, j] <= capacity[i, j], name=f"cap_{i}_{j}")

    nodes = range(6)
    for node in nodes:
        outflow = gp.quicksum(flow[i, j] for (i, j) in routes if i == node)
        inflow  = gp.quicksum(flow[i, j] for (i, j) in routes if j == node)
        model.addConstr(outflow - inflow == supply[node], name=f"flow_con_{node}")

    model.setObjective(
        gp.quicksum(cost[i, j] * flow[i, j] for (i, j) in routes),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}