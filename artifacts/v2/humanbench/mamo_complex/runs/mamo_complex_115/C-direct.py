import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_chicken = params["protein_chicken"]
    protein_rice    = params["protein_rice"]
    protein_tuna    = params["protein_tuna"]
    protein_beef    = params["protein_beef"]
    protein_corn    = params["protein_corn"]
    protein_whey    = params["protein_whey"]

    carbs_chicken = params["carbs_chicken"]
    carbs_rice    = params["carbs_rice"]
    carbs_tuna    = params["carbs_tuna"]
    carbs_beef    = params["carbs_beef"]
    carbs_corn    = params["carbs_corn"]
    carbs_whey    = params["carbs_whey"]

    calories_chicken = params["calories_chicken"]
    calories_rice    = params["calories_rice"]
    calories_tuna    = params["calories_tuna"]
    calories_beef    = params["calories_beef"]
    calories_corn    = params["calories_corn"]
    calories_whey    = params["calories_whey"]

    cost_chicken = params["cost_chicken"]
    cost_rice    = params["cost_rice"]
    cost_tuna    = params["cost_tuna"]
    cost_beef    = params["cost_beef"]
    cost_corn    = params["cost_corn"]
    cost_whey    = params["cost_whey"]

    target_protein  = params["target_protein"]
    target_carbs    = params["target_carbs"]
    target_calories = params["target_calories"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    x_chicken = model.addVar(lb=0.0, name="x_chicken")
    x_rice    = model.addVar(lb=0.0, name="x_rice")
    x_tuna    = model.addVar(lb=0.0, name="x_tuna")
    x_beef    = model.addVar(lb=0.0, name="x_beef")
    x_corn    = model.addVar(lb=0.0, name="x_corn")
    x_whey    = model.addVar(lb=0.0, name="x_whey")

    model.setObjective(
        cost_chicken * x_chicken +
        cost_rice    * x_rice    +
        cost_tuna    * x_tuna    +
        cost_beef    * x_beef    +
        cost_corn    * x_corn    +
        cost_whey    * x_whey,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_chicken * x_chicken +
        protein_rice    * x_rice    +
        protein_tuna    * x_tuna    +
        protein_beef    * x_beef    +
        protein_corn    * x_corn    +
        protein_whey    * x_whey    >= target_protein,
        name="protein_req"
    )

    model.addConstr(
        carbs_chicken * x_chicken +
        carbs_rice    * x_rice    +
        carbs_tuna    * x_tuna    +
        carbs_beef    * x_beef    +
        carbs_corn    * x_corn    +
        carbs_whey    * x_whey    >= target_carbs,
        name="carbs_req"
    )

    model.addConstr(
        calories_chicken * x_chicken +
        calories_rice    * x_rice    +
        calories_tuna    * x_tuna    +
        calories_beef    * x_beef    +
        calories_corn    * x_corn    +
        calories_whey    * x_whey   >= target_calories,
        name="calories_req"
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
        return {"objective": None, "status": f"gurobi_status_{status}"}