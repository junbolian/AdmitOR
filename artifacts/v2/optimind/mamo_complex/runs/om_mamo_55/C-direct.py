import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_goal = params["protein_goal"]
    carb_goal = params["carb_goal"]
    calorie_goal = params["calorie_goal"]

    cost_chicken = params["cost_chicken"]
    cost_rice = params["cost_rice"]
    cost_beans = params["cost_beans"]
    cost_avocado = params["cost_avocado"]

    protein_chicken = params["protein_chicken"]
    protein_rice = params["protein_rice"]
    protein_beans = params["protein_beans"]
    protein_avocado = params["protein_avocado"]

    carb_chicken = params["carb_chicken"]
    carb_rice = params["carb_rice"]
    carb_beans = params["carb_beans"]
    carb_avocado = params["carb_avocado"]

    cal_chicken = params["cal_chicken"]
    cal_rice = params["cal_rice"]
    cal_beans = params["cal_beans"]
    cal_avocado = params["cal_avocado"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x_chicken = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_chicken")
    x_rice = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_rice")
    x_beans = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_beans")
    x_avocado = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_avocado")

    model.setObjective(
        cost_chicken * x_chicken + cost_rice * x_rice + cost_beans * x_beans + cost_avocado * x_avocado,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_chicken * x_chicken + protein_rice * x_rice + protein_beans * x_beans + protein_avocado * x_avocado >= protein_goal,
        "protein"
    )
    model.addConstr(
        carb_chicken * x_chicken + carb_rice * x_rice + carb_beans * x_beans + carb_avocado * x_avocado >= carb_goal,
        "carbs"
    )
    model.addConstr(
        cal_chicken * x_chicken + cal_rice * x_rice + cal_beans * x_beans + cal_avocado * x_avocado >= calorie_goal,
        "calories"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}