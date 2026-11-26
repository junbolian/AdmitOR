import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken", "Rice", "Apples", "Steak", "Lentils", "Fish", "Tofu", "Cheese", "Bread"]

    protein_content = params["protein_content"]
    carb_content = params["carb_content"]
    calorie_content = params["calorie_content"]
    food_price = params["food_price"]
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    def prot(f):
        return protein_content[foods.index(f)]

    def carb(f):
        return carb_content[foods.index(f)]

    def cal(f):
        return calorie_content[foods.index(f)]

    def price(f):
        return food_price[foods.index(f)]

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)
    model.x = pyo.Var(model.FOODS, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(price(f) * model.x[f] for f in model.FOODS),
        sense=pyo.minimize,
    )

    model.protein_con = pyo.Constraint(
        expr=sum(prot(f) * model.x[f] for f in model.FOODS) >= protein_requirement
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carb(f) * model.x[f] for f in model.FOODS) >= carb_requirement
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(cal(f) * model.x[f] for f in model.FOODS) >= calorie_requirement
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}