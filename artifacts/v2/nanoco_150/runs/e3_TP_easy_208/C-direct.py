import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    capacity = params["capacity"]
    unit_cost = params["unit_cost"]
    # coords_x and coords_y are provided but not used in the optimization model
    # (they define geography, not the mathematical problem)

    # Arc definitions: 12 directed arcs from warehouses (0,1,2) to plants (3,4,5,6)
    arcs = [
        (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 3), (2, 4), (2, 5), (2, 6),
    ]

    nodes = list(range(7))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: flow on each arc
    flow = {}
    for idx, (i, j) in enumerate(arcs):
        flow[(i, j)] = model.addVar(
            lb=0.0,
            ub=capacity[idx],
            obj=unit_cost[idx],
            vtype=GRB.CONTINUOUS,
            name=f"flow_{i}_{j}"
        )

    model.ModelSense = GRB.MINIMIZE

    # Flow balance constraints: net outflow - net inflow = supply[node]
    for node in nodes:
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in arcs if i == node)
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in arcs if j == node)
        model.addConstr(outflow - inflow == supply[node], name=f"balance_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}