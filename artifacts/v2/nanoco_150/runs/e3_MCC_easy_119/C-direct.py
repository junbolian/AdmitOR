import gurobipy as gp
from gurobipy import GRB

def solve(params):
    coordinates = params["coordinates"]
    route_cost = params["route_cost"]
    route_min_flow = params["route_min_flow"]
    route_max_capacity = params["route_max_capacity"]

    # Route definitions (fixed structure)
    routes = [
        (0, 1), (0, 2), (0, 5),
        (1, 0), (1, 2),
        (2, 1), (2, 3),
        (3, 1), (3, 2), (3, 4),
        (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 2), (5, 3), (5, 4),
    ]
    num_routes = len(routes)
    num_nodes = 6

    model = gp.Model("empty_container_repositioning")
    model.setParam("OutputFlag", 0)

    # Decision variables: integer flow on each route
    flow = model.addVars(num_routes, lb=0, vtype=GRB.INTEGER, name="flow")

    # Bounds from params
    for r in range(num_routes):
        flow[r].lb = route_min_flow[r]
        flow[r].ub = route_max_capacity[r]

    # Flow conservation: inflow == outflow at every node
    for node in range(num_nodes):
        inflow = gp.quicksum(
            flow[r] for r, (src, dst) in enumerate(routes) if dst == node
        )
        outflow = gp.quicksum(
            flow[r] for r, (src, dst) in enumerate(routes) if src == node
        )
        model.addConstr(inflow == outflow, name=f"balance_node_{node}")

    # Objective: minimize total repositioning cost
    model.setObjective(
        gp.quicksum(route_cost[r] * flow[r] for r in range(num_routes)),
        GRB.MINIMIZE,
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