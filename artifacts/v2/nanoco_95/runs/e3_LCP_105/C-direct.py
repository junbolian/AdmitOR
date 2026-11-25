import gurobipy as gp
from gurobipy import GRB

def solve(params):
    slots = list(range(9))
    brands = list(range(9))

    permitted = {
        0: {0, 1, 2, 3, 4, 5, 6, 7, 8},
        1: {1, 2, 3, 5, 6, 7, 8},
        2: {0, 1, 2, 3, 4, 5, 6, 7, 8},
        3: {0, 3, 5, 6},
        4: {0, 1, 2, 3, 5, 6, 7, 8},
        5: {0, 3, 5, 7, 8},
        6: {0, 1, 2, 3, 4, 6, 7, 8},
        7: {3, 4, 5, 7, 8},
        8: {0, 1, 2, 4, 5, 6, 7, 8},
    }

    edges = [
        (0, 1), (3, 4), (2, 7), (1, 8), (2, 3),
        (1, 7), (0, 5), (4, 8), (2, 5), (1, 3),
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[s, b] = 1 if slot s is assigned brand b
    x = {}
    for s in slots:
        for b in brands:
            if b in permitted[s]:
                x[s, b] = model.addVar(vtype=GRB.BINARY, name=f"x_{s}_{b}")

    # z = max brand identifier used
    z = model.addVar(vtype=GRB.INTEGER, lb=0, ub=8, name="z")

    # Objective: minimize z
    model.setObjective(z, GRB.MINIMIZE)

    # Each slot assigned exactly one permitted brand
    for s in slots:
        model.addConstr(
            gp.quicksum(x[s, b] for b in brands if (s, b) in x) == 1,
            name=f"assign_{s}"
        )

    # z >= b * x[s, b] for all s, b  =>  z is at least the assigned brand
    for s in slots:
        for b in brands:
            if (s, b) in x:
                model.addConstr(z >= b * x[s, b], name=f"zbound_{s}_{b}")

    # Adjacency: adjacent slots cannot share a brand
    for (s1, s2) in edges:
        for b in brands:
            if (s1, b) in x and (s2, b) in x:
                model.addConstr(
                    x[s1, b] + x[s2, b] <= 1,
                    name=f"adj_{s1}_{s2}_{b}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}