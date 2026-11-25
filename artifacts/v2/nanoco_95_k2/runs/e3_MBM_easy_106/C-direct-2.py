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
        # solar farm 6 has no feasible lines
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable for each feasible transmission line
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Maximize number of matched pairs
    model.setObjective(gp.quicksum(x[e] for e in edges), GRB.MAXIMIZE)

    # Each solar farm dispatches to at most one substation
    farms = range(7)
    for f in farms:
        farm_edges = [e for e in edges if e[0] == f]
        if farm_edges:
            model.addConstr(gp.quicksum(x[e] for e in farm_edges) <= 1, name=f"farm_{f}")

    # Each substation receives from at most one solar farm
    substations = range(5)
    for s in substations:
        sub_edges = [e for e in edges if e[1] == s]
        if sub_edges:
            model.addConstr(gp.quicksum(x[e] for e in sub_edges) <= 1, name=f"sub_{s}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}