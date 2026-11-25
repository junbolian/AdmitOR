import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost_team1 = float(params["cost_team1"])
    cost_team2 = float(params["cost_team2"])
    cost_team3 = float(params["cost_team3"])

    coef_sel1_sel3 = float(params["coef_sel1_sel3"])
    rhs_sel1_sel3 = float(params["rhs_sel1_sel3"])

    coef_sel1_sel2 = float(params["coef_sel1_sel2"])
    rhs_sel1_sel2 = float(params["rhs_sel1_sel2"])

    coef_sel2_single = float(params["coef_sel2_single"])
    rhs_sel2_single = float(params["rhs_sel2_single"])

    coef_all_three = float(params["coef_all_three"])
    rhs_all_three = float(params["rhs_all_three"])

    coef_sel3_single = float(params["coef_sel3_single"])
    rhs_sel3_single = float(params["rhs_sel3_single"])

    coef_sel2_sel3 = float(params["coef_sel2_sel3"])
    rhs_sel2_sel3 = float(params["rhs_sel2_sel3"])

    coef_sel1_single = float(params["coef_sel1_single"])
    rhs_sel1_single = float(params["rhs_sel1_single"])

    model = gp.Model("emergency_response")
    model.setParam("OutputFlag", 0)

    s1 = model.addVar(vtype=GRB.BINARY, name="Selected_1")
    s2 = model.addVar(vtype=GRB.BINARY, name="Selected_2")
    s3 = model.addVar(vtype=GRB.BINARY, name="Selected_3")

    model.setObjective(cost_team1 * s1 + cost_team2 * s2 + cost_team3 * s3, GRB.MINIMIZE)

    for tag in ["e1", "e6", "e9", "e23"]:
        model.addConstr(
            coef_sel1_sel3 * s1 + coef_sel1_sel3 * s3 >= rhs_sel1_sel3,
            name=f"MultiCover_{tag}"
        )

    for tag in ["e2", "e5", "e14", "e19", "e20"]:
        model.addConstr(
            coef_sel1_sel2 * s1 + coef_sel1_sel2 * s2 >= rhs_sel1_sel2,
            name=f"MultiCover_{tag}"
        )

    for tag in ["e3", "e8", "e10", "e25", "e26"]:
        model.addConstr(
            coef_sel2_single * s2 >= rhs_sel2_single,
            name=f"MultiCover_{tag}"
        )

    for tag in ["e4", "e7", "e13", "e17", "e21", "e22", "e24", "e27"]:
        model.addConstr(
            coef_all_three * s1 + coef_all_three * s2 + coef_all_three * s3 >= rhs_all_three,
            name=f"MultiCover_{tag}"
        )

    for tag in ["e11", "e16", "e18"]:
        model.addConstr(
            coef_sel3_single * s3 >= rhs_sel3_single,
            name=f"MultiCover_{tag}"
        )

    model.addConstr(
        coef_sel2_sel3 * s2 + coef_sel2_sel3 * s3 >= rhs_sel2_sel3,
        name="MultiCover_e12"
    )

    for tag in ["e15", "e20_sel1"]:
        model.addConstr(
            coef_sel1_single * s1 >= rhs_sel1_single,
            name=f"MultiCover_{tag}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}