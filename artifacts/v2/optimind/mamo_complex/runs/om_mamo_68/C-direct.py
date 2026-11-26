import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_chicken = params["protein_chicken"]
    carb_chicken    = params["carb_chicken"]
    cal_chicken     = params["cal_chicken"]
    cost_chicken    = params["cost_chicken"]

    protein_rice    = params["protein_rice"]
    carb_rice       = params["carb_rice"]
    cal_rice        = params["cal_rice"]
    cost_rice       = params["cost_rice"]

    protein_tuna    = params["protein_tuna"]
    carb_tuna       = params["carb_tuna"]
    cal_tuna        = params["cal_tuna"]
    cost_tuna       = params["cost_tuna"]

    protein_beef    = params["protein_beef"]
    carb_beef       = params["carb_beef"]
    cal_beef        = params["cal_beef"]
    cost_beef       = params["cost_beef"]

    protein_corn    = params["protein_corn"]
    carb_corn       = params["carb_corn"]
    cal_corn        = params["cal_corn"]
    cost_corn       = params["cost_corn"]

    protein_whey    = params["protein_whey"]
    carb_whey       = params["carb_whey"]
    cal_whey        = params["cal_whey"]
    cost_whey       = params["cost_whey"]

    protein_target  = params["protein_target"]
    carb_target     = params["carb_target"]
    cal_target      = params["cal_target"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    chicken = model.addVar(vtype=GRB.INTEGER, lb=0, name="chicken")
    rice    = model.addVar(vtype=GRB.INTEGER, lb=0, name="rice")
    tuna    = model.addVar(vtype=GRB.INTEGER, lb=0, name="tuna")
    beef    = model.addVar(vtype=GRB.INTEGER, lb=0, name="beef")
    corn    = model.addVar(vtype=GRB.INTEGER, lb=0, name="corn")
    whey    = model.addVar(vtype=GRB.INTEGER, lb=0, name="whey")

    model.setObjective(
        cost_chicken * chicken +
        cost_rice    * rice    +
        cost_tuna    * tuna    +
        cost_beef    * beef    +
        cost_corn    * corn    +
        cost_whey    * whey,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_chicken * chicken +
        protein_rice    * rice    +
        protein_tuna    * tuna    +
        protein_beef    * beef    +
        protein_corn    * corn    +
        protein_whey    * whey    >= protein_target,
        name="protein"
    )

    model.addConstr(
        carb_chicken * chicken +
        carb_rice    * rice    +
        carb_tuna    * tuna    +
        carb_beef    * beef    +
        carb_corn    * corn    +
        carb_whey    * whey    >= carb_target,
        name="carbs"
    )

    model.addConstr(
        cal_chicken * chicken +
        cal_rice    * rice    +
        cal_tuna    * tuna    +
        cal_beef    * beef    +
        cal_corn    * corn    +
        cal_whey    * whey    >= cal_target,
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