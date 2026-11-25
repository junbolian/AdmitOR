import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Feasible transmission lines: (solar_farm, substation)
    edges = [
        (0, 1), (0, 2),
        (1, 0), (1, 3),
        (2, 2), (2, 3),
        (3, 1), (3, 2), (3, 3), (3, 4),
        (4, 0), (4, 1),
        (5, 3),
    ]

    farms = range(7)
    substations = range(5)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: assign solar farm i to substation j
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Maximize number of matched pairs
    model.setObjective(gp.quicksum(x[e] for e in edges), GRB.MAXIMIZE)

    # Each solar farm dispatches to at most one substation
    for i in farms:
        farm_edges = [e for e in edges if e[0] == i]
        if farm_edges:
            model.addConstr(gp.quicksum(x[e] for e in farm_edges) <= 1, name=f"farm_{i}")

    # Each substation receives from at most one solar farm
    for j in substations:
        sub_edges = [e for e in edges if e[1] == j]
        if sub_edges:
            model.addConstr(gp.quicksum(x[e] for e in sub_edges) <= 1, name=f"sub_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}