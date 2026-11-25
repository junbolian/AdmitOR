import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = [
        params["cost_area_1"],
        params["cost_area_2"],
        params["cost_area_3"],
        params["cost_area_4"],
        params["cost_area_5"],
    ]

    # Coverage matrix: coverage[i] = list of area indices (0-based) covering ecosystem i
    coverage = [
        [0, 1],        # e1: area1 or area2
        [2, 3],        # e2: area3 or area4
        [1, 2],        # e3: area2 or area3
        [1, 2],        # e4: area2 or area3
        [1, 2, 3],     # e5: area2, area3, or area4
        [0],           # e6: area1
        [1, 2, 3],     # e7: area2, area3, or area4
        [2, 3],        # e8: area3 or area4
        [1, 2],        # e9: area2 or area3
        [0, 4],        # e10: area1 or area5
        [1, 3],        # e11: area2 or area4
        [2, 4],        # e12: area3 or area5
        [2, 3],        # e13: area3 or area4
        [3],           # e14: area4
        [0, 3, 4],     # e15: area1, area4, or area5
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(5, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(cost[a] * x[a] for a in range(5)), GRB.MINIMIZE)

    for idx, areas in enumerate(coverage):
        model.addConstr(gp.quicksum(x[a] for a in areas) >= 1, name=f"eco_{idx+1}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}