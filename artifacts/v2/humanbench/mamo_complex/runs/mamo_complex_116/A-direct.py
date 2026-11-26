import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    food_names = ["Chicken", "Rice", "Eggs", "Beans", "Spinach", "Corn", "Beef", "Broccoli"]

    food_cost = params["food_cost"]
    protein_content = params["protein_content"]
    carb_content = params["carb_content"]
    calorie_content = params["calorie_content"]
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=food_names)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    model.total_cost = pyo.Objective(
        expr=sum(food_cost[food_names.index(f)] * model.x[f] for f in model.FOODS),
        sense=pyo.minimize,
    )

    model.protein_con = pyo.Constraint(
        expr=sum(protein_content[food_names.index(f)] * model.x[f] for f in model.FOODS) >= protein_requirement
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carb_content[food_names.index(f)] * model.x[f] for f in model.FOODS) >= carb_requirement
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calorie_content[food_names.index(f)] * model.x[f] for f in model.FOODS) >= calorie_requirement
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}