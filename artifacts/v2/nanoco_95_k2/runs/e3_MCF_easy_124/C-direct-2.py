import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    capacity = params["capacity"]
    cost = params["cost"]
    coords = params["coords"]

    arcs = [(0, 2), (0, 3), (1, 2), (1, 3),
            (2, 4), (2, 5), (3, 4), (3, 5),
            (0, 4), (0, 5), (1, 4), (1, 5)]
    nodes = list(range(6))

    model = gp.Model("food_redistribution")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(len(arcs)):
        x[i] = model.addVar(lb=0.0, ub=float(capacity[i]), name=f"x_{i}")

    for n in nodes:
        outflow = gp.quicksum(x[i] for i in range(len(arcs)) if arcs[i][0] == n)
        inflow = gp.quicksum(x[i] for i in range(len(arcs)) if arcs[i][1] == n)
        model.addConstr(outflow - inflow == float(supply[n]), name=f"flow_{n}")

    model.setObjective(
        gp.quicksum(float(cost[i]) * x[i] for i in range(len(arcs))),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "no_optimal"}