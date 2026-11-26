import gurobipy as gp
from gurobipy import GRB


def solve(params):
    foods = ["bread", "milk", "fish", "potato"]
    protein = {
        "bread": params["protein_bread"],
        "milk": params["protein_milk"],
        "fish": params["protein_fish"],
        "potato": params["protein_potato"],
    }
    carb = {
        "bread": params["carb_bread"],
        "milk": params["carb_milk"],
        "fish": params["carb_fish"],
        "potato": params["carb_potato"],
    }
    calorie = {
        "bread": params["calorie_bread"],
        "milk": params["calorie_milk"],
        "fish": params["calorie_fish"],
        "potato": params["calorie_potato"],
    }
    cost = {
        "bread": params["cost_bread"],
        "milk": params["cost_milk"],
        "fish": params["cost_fish"],
        "potato": params["cost_potato"],
    }

    model = gp.Model("diet")
    x = model.addVars(foods, lb=0, name="x")

    model.setObjective(
        gp.quicksum(cost[f] * x[f] for f in foods), GRB.MINIMIZE
    )

    model.addConstr(
        gp.quicksum(protein[f] * x[f] for f in foods)
        >= params["req_protein"],
        "min_protein",
    )
    model.addConstr(
        gp.quicksum(carb[f] * x[f] for f in foods) >= params["req_carbs"],
        "min_carbs",
    )
    model.addConstr(
        gp.quicksum(calorie[f] * x[f] for f in foods)
        >= params["req_calories"],
        "min_calories",
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "infeasible"}