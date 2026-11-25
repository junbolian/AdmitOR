import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost_team1 = float(params["cost_team1"])
    cost_team2 = float(params["cost_team2"])
    cost_team3 = float(params["cost_team3"])

    coef_sel1_sel3 = float(params["coef_sel1_sel3"])
    rhs_sel1_sel3  = float(params["rhs_sel1_sel3"])

    coef_sel1_sel2 = float(params["coef_sel1_sel2"])
    rhs_sel1_sel2  = float(params["rhs_sel1_sel2"])

    coef_sel2_single = float(params["coef_sel2_single"])
    rhs_sel2_single  = float(params["rhs_sel2_single"])

    coef_all_three = float(params["coef_all_three"])
    rhs_all_three  = float(params["rhs_all_three"])

    coef_sel3_single = float(params["coef_sel3_single"])
    rhs_sel3_single  = float(params["rhs_sel3_single"])

    coef_sel2_sel3 = float(params["coef_sel2_sel3"])
    rhs_sel2_sel3  = float(params["rhs_sel2_sel3"])

    coef_sel1_single = float(params["coef_sel1_single"])
    rhs_sel1_single  = float(params["rhs_sel1_single"])

    model = gp.Model("emergency_teams")
    model.setParam("OutputFlag", 0)

    s1 = model.addVar(vtype=GRB.BINARY, name="Selected_1")
    s2 = model.addVar(vtype=GRB.BINARY, name="Selected_2")
    s3 = model.addVar(vtype=GRB.BINARY, name="Selected_3")

    model.setObjective(cost_team1 * s1 + cost_team2 * s2 + cost_team3 * s3, GRB.MINIMIZE)

    # Selected[1] + Selected[3] >= rhs_sel1_sel3  (e1, e6, e9, e23)
    model.addConstr(coef_sel1_sel3 * s1 + coef_sel1_sel3 * s3 >= rhs_sel1_sel3, "MultiCover_e1")
    model.addConstr(coef_sel1_sel3 * s1 + coef_sel1_sel3 * s3 >= rhs_sel1_sel3, "MultiCover_e6")
    model.addConstr(coef_sel1_sel3 * s1 + coef_sel1_sel3 * s3 >= rhs_sel1_sel3, "MultiCover_e9")
    model.addConstr(coef_sel1_sel3 * s1 + coef_sel1_sel3 * s3 >= rhs_sel1_sel3, "MultiCover_e23")

    # Selected[1] + Selected[2] >= rhs_sel1_sel2  (e2, e5, e14, e19, e20)
    model.addConstr(coef_sel1_sel2 * s1 + coef_sel1_sel2 * s2 >= rhs_sel1_sel2, "MultiCover_e2")
    model.addConstr(coef_sel1_sel2 * s1 + coef_sel1_sel2 * s2 >= rhs_sel1_sel2, "MultiCover_e5")
    model.addConstr(coef_sel1_sel2 * s1 + coef_sel1_sel2 * s2 >= rhs_sel1_sel2, "MultiCover_e14")
    model.addConstr(coef_sel1_sel2 * s1 + coef_sel1_sel2 * s2 >= rhs_sel1_sel2, "MultiCover_e19")
    model.addConstr(coef_sel1_sel2 * s1 + coef_sel1_sel2 * s2 >= rhs_sel1_sel2, "MultiCover_e20a")

    # Selected[2] >= rhs_sel2_single  (e3, e8, e10, e25, e26)
    model.addConstr(coef_sel2_single * s2 >= rhs_sel2_single, "MultiCover_e3")
    model.addConstr(coef_sel2_single * s2 >= rhs_sel2_single, "MultiCover_e8")
    model.addConstr(coef_sel2_single * s2 >= rhs_sel2_single, "MultiCover_e10")
    model.addConstr(coef_sel2_single * s2 >= rhs_sel2_single, "MultiCover_e25")
    model.addConstr(coef_sel2_single * s2 >= rhs_sel2_single, "MultiCover_e26")

    # Selected[1] + Selected[2] + Selected[3] >= rhs_all_three  (e4, e7, e13, e17, e21, e22, e24, e27)
    model.addConstr(coef_all_three * s1 + coef_all_three * s2 + coef_all_three * s3 >= rhs_all_three, "MultiCover_e4")
    model.addConstr(coef_all_three * s1 + coef_all_three * s2 + coef_all_three * s3 >= rhs_all_three, "MultiCover_e7")
    model.addConstr(coef_all_three * s1 + coef_all_three * s2 + coef_all_three * s3 >= rhs_all_three, "MultiCover_e13")
    model.addConstr(coef_all_three * s1 + coef_all_three * s2 + coef_all_three * s3 >= rhs_all_three, "MultiCover_e17")
    model.addConstr(coef_all_three * s1 + coef_all_three * s2 + coef_all_three * s3 >= rhs_all_three, "MultiCover_e21")
    model.addConstr(coef_all_three * s1 + coef_all_three * s2 + coef_all_three * s3 >= rhs_all_three, "MultiCover_e22")
    model.addConstr(coef_all_three * s1 + coef_all_three * s2 + coef_all_three * s3 >= rhs_all_three, "MultiCover_e24")
    model.addConstr(coef_all_three * s1 + coef_all_three * s2 + coef_all_three * s3 >= rhs_all_three, "MultiCover_e27")

    # Selected[3] >= rhs_sel3_single  (e11, e16, e18)
    model.addConstr(coef_sel3_single * s3 >= rhs_sel3_single, "MultiCover_e11")
    model.addConstr(coef_sel3_single * s3 >= rhs_sel3_single, "MultiCover_e16")
    model.addConstr(coef_sel3_single * s3 >= rhs_sel3_single, "MultiCover_e18")

    # Selected[2] + Selected[3] >= rhs_sel2_sel3  (e12)
    model.addConstr(coef_sel2_sel3 * s2 + coef_sel2_sel3 * s3 >= rhs_sel2_sel3, "MultiCover_e12")

    # Selected[1] >= rhs_sel1_single  (e15, e20)
    model.addConstr(coef_sel1_single * s1 >= rhs_sel1_single, "MultiCover_e15")
    model.addConstr(coef_sel1_single * s1 >= rhs_sel1_single, "MultiCover_e20b")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}