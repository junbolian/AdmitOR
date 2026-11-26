import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken", "Rice", "Broccoli", "Tofu", "Beans"]

    protein = params["protein_content"]
    carbs = params["carb_content"]
    calories = params["calorie_content"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)

    model.amount = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.amount[f] for i, f in enumerate(foods)) >= params["protein_requirement"]
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs[i] * model.amount[f] for i, f in enumerate(foods)) >= params["carb_requirement"]
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories[i] * model.amount[f] for i, f in enumerate(foods)) >= params["calorie_requirement"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[i] * model.amount[f] for i, f in enumerate(foods)),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception as exc:
        return {"objective": None, "status": "solve failed: " + type(exc).__name__}

    return {"objective": obj_val, "status": "optimal"}