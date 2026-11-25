import gurobipy as gp
from gurobipy import GRB

def solve(params):
    route_cost = params["route_cost"]
    route_min = params["route_min"]
    route_max = params["route_max"]

    # Routes in order: (from, to)
    routes = [
        (0, 1), (0, 2), (0, 5),
        (1, 0), (1, 2), (1, 5),
        (2, 1), (2, 3), (2, 5),
        (3, 0), (3, 1), (3, 2), (3, 4),
        (4, 3), (4, 5),
        (5, 0), (5, 2), (5, 4),
    ]

    num_routes = len(routes)
    warehouses = range(6)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = [
        model.addVar(lb=route_min[i], ub=route_max[i], vtype=GRB.INTEGER, name=f"x_{i}")
        for i in range(num_routes)
    ]

    # Flow balance: inflow == outflow for each warehouse
    for w in warehouses:
        inflow = gp.quicksum(x[i] for i, (src, dst) in enumerate(routes) if dst == w)
        outflow = gp.quicksum(x[i] for i, (src, dst) in enumerate(routes) if src == w)
        model.addConstr(inflow == outflow, name=f"balance_{w}")

    model.setObjective(
        gp.quicksum(route_cost[i] * x[i] for i in range(num_routes)),
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