import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost_team1 = params["cost_team1"]
    cost_team2 = params["cost_team2"]
    cost_team3 = params["cost_team3"]
    rhs_1_3 = params["rhs_1_3"]
    rhs_1_2 = params["rhs_1_2"]
    rhs_2_only = params["rhs_2_only"]
    rhs_1_2_3 = params["rhs_1_2_3"]
    rhs_3_only = params["rhs_3_only"]
    rhs_2_3 = params["rhs_2_3"]
    rhs_1_only = params["rhs_1_only"]

    model = gp.Model("emergency_teams")
    model.setParam("OutputFlag", 0)

    s1 = model.addVar(vtype=GRB.BINARY, name="Selected_1")
    s2 = model.addVar(vtype=GRB.BINARY, name="Selected_2")
    s3 = model.addVar(vtype=GRB.BINARY, name="Selected_3")

    model.setObjective(cost_team1 * s1 + cost_team2 * s2 + cost_team3 * s3, GRB.MINIMIZE)

    # Selected[1] + Selected[3] >= rhs_1_3
    for tag in ["e1", "e6", "e9", "e23"]:
        model.addConstr(s1 + s3 >= rhs_1_3, name=f"MultiCover_{tag}")

    # Selected[1] + Selected[2] >= rhs_1_2
    for tag in ["e2", "e5", "e14", "e19", "e20a"]:
        model.addConstr(s1 + s2 >= rhs_1_2, name=f"MultiCover_{tag}")

    # Selected[2] >= rhs_2_only
    for tag in ["e3", "e8", "e10", "e25", "e26"]:
        model.addConstr(s2 >= rhs_2_only, name=f"MultiCover_{tag}")

    # Selected[1] + Selected[2] + Selected[3] >= rhs_1_2_3
    for tag in ["e4", "e7", "e13", "e17", "e21", "e22", "e24", "e27"]:
        model.addConstr(s1 + s2 + s3 >= rhs_1_2_3, name=f"MultiCover_{tag}")

    # Selected[3] >= rhs_3_only
    for tag in ["e11", "e16", "e18"]:
        model.addConstr(s3 >= rhs_3_only, name=f"MultiCover_{tag}")

    # Selected[2] + Selected[3] >= rhs_2_3
    model.addConstr(s2 + s3 >= rhs_2_3, name="MultiCover_e12")

    # Selected[1] >= rhs_1_only
    for tag in ["e15", "e20b"]:
        model.addConstr(s1 >= rhs_1_only, name=f"MultiCover_{tag}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}