import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["chicken_breast", "tofu", "spinach", "beef_steak",
             "eggs", "brown_rice", "bananas", "quinoa"]

    cost_list = params["cost"]
    protein_list = params["protein"]
    carbs_list = params["carbs"]
    calories_list = params["calories"]
    protein_req = params["protein_requirement"]
    carb_req = params["carb_requirement"]
    calorie_req = params["calorie_requirement"]

    def _as_map(values):
        if isinstance(values, dict):
            return {foods[i]: values[foods[i]] for i in range(len(foods))}
        return {foods[i]: values[i] for i in range(len(foods))}

    cost = _as_map(cost_list)
    protein = _as_map(protein_list)
    carbs = _as_map(carbs_list)
    calories = _as_map(calories_list)

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods)

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.cost_expr = pyo.Expression(
        expr=sum(cost[f] * model.portions[f] for f in model.foods)
    )

    model.protein_rule = pyo.Constraint(
        expr=sum(protein[f] * model.portions[f] for f in model.foods) >= protein_req
    )
    model.carb_rule = pyo.Constraint(
        expr=sum(carbs[f] * model.portions[f] for f in model.foods) >= carb_req
    )
    model.calorie_rule = pyo.Constraint(
        expr=sum(calories[f] * model.portions[f] for f in model.foods) >= calorie_req
    )

    model.obj = pyo.Objective(expr=model.cost_expr, sense=pyo.minimize)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}