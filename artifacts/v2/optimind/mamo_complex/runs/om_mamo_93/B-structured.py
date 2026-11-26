# IR: {"sets":{"foods":["Food_1","Food_2","Food_3","Food_4"]},"params":{"protein_content":"food-indexed","carb_content":"food-indexed","calorie_content":"food-indexed","cost":"food-indexed","protein_requirement":"scalar","carb_requirement":"scalar","calorie_requirement":"scalar"},"variables":{"portions[food]":"nonnegative integer"},"constraints":["sum(protein_content[food]*portions[food]) >= protein_requirement","sum(carb_content[food]*portions[food]) >= carb_requirement","sum(calorie_content[food]*portions[food]) >= calorie_requirement"],"objective":"minimize sum(cost[food]*portions[food])"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Food-indexed inputs accept Food_1..Food_4 mappings or ordered sequences."""
    foods = ("Food_1", "Food_2", "Food_3", "Food_4")

    def food_data(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        return {
            food: values[position]
            for position, food in enumerate(foods)
        }

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein_content = pyo.Param(
        model.foods, initialize=food_data(params["protein_content"])
    )
    model.carb_content = pyo.Param(
        model.foods, initialize=food_data(params["carb_content"])
    )
    model.calorie_content = pyo.Param(
        model.foods, initialize=food_data(params["calorie_content"])
    )
    model.cost = pyo.Param(
        model.foods, initialize=food_data(params["cost"])
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
        # APPsi raises this when automatic solution loading has no solution.
        # Leave success determination to objective retrieval below.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}