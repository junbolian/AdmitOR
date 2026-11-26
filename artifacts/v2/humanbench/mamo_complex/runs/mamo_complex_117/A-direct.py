import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["chicken", "rice", "broccoli", "eggs"]

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    model.protein = pyo.Constraint(
        expr=sum(params["protein_" + f] * model.x[f] for f in foods)
        >= params["protein_requirement"]
    )
    model.carbs = pyo.Constraint(
        expr=sum(params["carbs_" + f] * model.x[f] for f in foods)
        >= params["carb_requirement"]
    )
    model.calories = pyo.Constraint(
        expr=sum(params["calories_" + f] * model.x[f] for f in foods)
        >= params["calorie_requirement"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(params["cost_" + f] * model.x[f] for f in foods),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}