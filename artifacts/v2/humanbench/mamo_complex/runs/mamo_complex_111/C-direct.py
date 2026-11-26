import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_chicken = params["protein_chicken"]
    protein_cheese  = params["protein_cheese"]
    protein_rice    = params["protein_rice"]
    protein_beans   = params["protein_beans"]

    carbs_chicken = params["carbs_chicken"]
    carbs_cheese  = params["carbs_cheese"]
    carbs_rice    = params["carbs_rice"]
    carbs_beans   = params["carbs_beans"]

    calories_chicken = params["calories_chicken"]
    calories_cheese  = params["calories_cheese"]
    calories_rice    = params["calories_rice"]
    calories_beans   = params["calories_beans"]

    price_chicken = params["price_chicken"]
    price_cheese  = params["price_cheese"]
    price_rice    = params["price_rice"]
    price_beans   = params["price_beans"]

    protein_req  = params["protein_req"]
    carbs_req    = params["carbs_req"]
    calories_req = params["calories_req"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    x_chicken = model.addVar(lb=0.0, name="x_chicken")
    x_cheese  = model.addVar(lb=0.0, name="x_cheese")
    x_rice    = model.addVar(lb=0.0, name="x_rice")
    x_beans   = model.addVar(lb=0.0, name="x_beans")

    model.setObjective(
        price_chicken * x_chicken +
        price_cheese  * x_cheese  +
        price_rice    * x_rice    +
        price_beans   * x_beans,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_chicken * x_chicken +
        protein_cheese  * x_cheese  +
        protein_rice    * x_rice    +
        protein_beans   * x_beans   >= protein_req,
        "protein"
    )

    model.addConstr(
        carbs_chicken * x_chicken +
        carbs_cheese  * x_cheese  +
        carbs_rice    * x_rice    +
        carbs_beans   * x_beans   >= carbs_req,
        "carbs"
    )

    model.addConstr(
        calories_chicken * x_chicken +
        calories_cheese  * x_cheese  +
        calories_rice    * x_rice    +
        calories_beans   * x_beans   >= calories_req,
        "calories"
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