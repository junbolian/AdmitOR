import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_chicken  = params["protein_chicken"]
    protein_rice     = params["protein_rice"]
    protein_beans    = params["protein_beans"]
    protein_broccoli = params["protein_broccoli"]
    protein_fruit    = params["protein_fruit"]

    carbs_chicken    = params["carbs_chicken"]
    carbs_rice       = params["carbs_rice"]
    carbs_beans      = params["carbs_beans"]
    carbs_broccoli   = params["carbs_broccoli"]
    carbs_fruit      = params["carbs_fruit"]

    calories_chicken  = params["calories_chicken"]
    calories_rice     = params["calories_rice"]
    calories_beans    = params["calories_beans"]
    calories_broccoli = params["calories_broccoli"]
    calories_fruit    = params["calories_fruit"]

    cost_chicken     = params["cost_chicken"]
    cost_rice        = params["cost_rice"]
    cost_beans       = params["cost_beans"]
    cost_broccoli    = params["cost_broccoli"]
    cost_fruit       = params["cost_fruit"]

    min_protein  = params["min_protein"]
    min_carbs    = params["min_carbs"]
    min_calories = params["min_calories"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    x_chicken  = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_chicken")
    x_rice     = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_rice")
    x_beans    = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_beans")
    x_broccoli = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_broccoli")
    x_fruit    = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_fruit")

    model.setObjective(
        cost_chicken  * x_chicken +
        cost_rice     * x_rice    +
        cost_beans    * x_beans   +
        cost_broccoli * x_broccoli +
        cost_fruit    * x_fruit,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_chicken  * x_chicken +
        protein_rice     * x_rice    +
        protein_beans    * x_beans   +
        protein_broccoli * x_broccoli +
        protein_fruit    * x_fruit   >= min_protein,
        name="protein"
    )

    model.addConstr(
        carbs_chicken    * x_chicken +
        carbs_rice       * x_rice    +
        carbs_beans      * x_beans   +
        carbs_broccoli   * x_broccoli +
        carbs_fruit      * x_fruit   >= min_carbs,
        name="carbs"
    )

    model.addConstr(
        calories_chicken  * x_chicken +
        calories_rice     * x_rice    +
        calories_beans    * x_beans   +
        calories_broccoli * x_broccoli +
        calories_fruit    * x_fruit   >= min_calories,
        name="calories"
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