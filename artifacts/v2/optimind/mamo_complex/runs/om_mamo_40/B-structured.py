# IR: {"sets":{"foods":["Chicken","Rice","Apples","Cheese","Tofu"]},"params":{"protein_content":"grams/portion indexed by foods","carb_content":"grams/portion indexed by foods","calorie_content":"calories/portion indexed by foods","cost":"dollars/portion indexed by foods","protein_requirement":"minimum grams","carb_requirement":"minimum grams","calorie_requirement":"minimum calories"},"variables":{"portions[food]":"nonnegative integer"},"constraints":["sum(protein_content[f]*portions[f] for f in foods) >= protein_requirement","sum(carb_content[f]*portions[f] for f in foods) >= carb_requirement","sum(calorie_content[f]*portions[f] for f in foods) >= calorie_requirement"],"objective":"minimize sum(cost[f]*portions[f] for f in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("Chicken", "Rice", "Apples", "Cheese", "Tofu")

    def food_values(values):
        """Accept food-name mappings or sequences in the declared food order."""
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein_content = pyo.Param(
        model.foods, initialize=food_values(params["protein_content"])
    )
    model.carb_content = pyo.Param(
        model.foods, initialize=food_values(params["carb_content"])
    )
    model.calorie_content = pyo.Param(
        model.foods, initialize=food_values(params["calorie_content"])
    )
    model.cost = pyo.Param(
        model.foods, initialize=food_values(params["cost"])
    )
    model.protein_requirement = pyo.Param(
        initialize=params["protein_requirement"]
    )
    model.carb_requirement = pyo.Param(
        initialize=params["carb_requirement"]
    )
    model.calorie_requirement = pyo.Param(
        initialize=params["calorie_requirement"]
    )

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_target = pyo.Constraint(
        expr=sum(
            model.protein_content[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_requirement
    )
    model.carb_target = pyo.Constraint(
        expr=sum(
            model.carb_content[food] * model.portions[food]
            for food in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_target = pyo.Constraint(
        expr=sum(
            model.calorie_content[food] * model.portions[food]
            for food in model.foods
        ) >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.portions[food]
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