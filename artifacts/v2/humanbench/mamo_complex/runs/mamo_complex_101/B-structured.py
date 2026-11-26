# IR: {"sets":{"foods":["Steak","Tofu","Chicken","Broccoli","Rice","Spinach"]},"params":{"protein":"grams/unit, indexed by foods","carbs":"grams/unit, indexed by foods","calories":"calories/unit, indexed by foods","cost":"dollars/unit, indexed by foods","protein_req":"minimum protein","carb_req":"minimum carbohydrates","calorie_req":"minimum calories"},"variables":{"quantity[foods]":"continuous, nonnegative"},"constraints":["sum(protein[f]*quantity[f] for f in foods) >= protein_req","sum(carbs[f]*quantity[f] for f in foods) >= carb_req","sum(calories[f]*quantity[f] for f in foods) >= calorie_req"],"objective":"minimize sum(cost[f]*quantity[f] for f in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Indexed parameters accept food-name mappings or sequences in food order."""
    foods = ("Steak", "Tofu", "Chicken", "Broccoli", "Rice", "Spinach")

    def food_data(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        values = tuple(values)
        if len(values) != len(foods):
            raise ValueError("Each indexed parameter must contain six values.")
        return dict(zip(foods, values))

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein = pyo.Param(
        model.foods, initialize=food_data(params["protein"])
    )
    model.carbs = pyo.Param(
        model.foods, initialize=food_data(params["carbs"])
    )
    model.calories = pyo.Param(
        model.foods, initialize=food_data(params["calories"])
    )
    model.cost = pyo.Param(
        model.foods, initialize=food_data(params["cost"])
    )
    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carb_req = pyo.Param(initialize=params["carb_req"])
    model.calorie_req = pyo.Param(initialize=params["calorie_req"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_req
    )
    model.carbohydrate_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carb_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.quantity[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}