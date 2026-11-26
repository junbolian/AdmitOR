# IR: {"sets":{"foods":["Food_1","Food_2","Food_3","Food_4","Food_5"]},"params":{"protein_content":"foods -> grams/portion","carb_content":"foods -> grams/portion","calorie_content":"foods -> calories/portion","food_cost":"foods -> dollars/portion","protein_target":"minimum protein grams","carb_target":"minimum carbohydrate grams","calorie_target":"minimum calories"},"input_format":"Indexed parameters accept five-element sequences or mappings keyed by food names, zero-based integers, or one-based integers; sequences follow foods order.","variables":{"portions[food]":"NonNegativeIntegers"},"constraints":["sum(protein_content[food]*portions[food] for food in foods) >= protein_target","sum(carb_content[food]*portions[food] for food in foods) >= carb_target","sum(calorie_content[food]*portions[food] for food in foods) >= calorie_target"],"objective":"minimize sum(food_cost[food]*portions[food] for food in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _normalize_food_values(values, foods, parameter_name):
    """Convert supported indexed inputs into a food-keyed dictionary."""
    if isinstance(values, Mapping):
        if len(values) != len(foods):
            raise ValueError(
                f"{parameter_name} must contain exactly {len(foods)} entries."
            )

        if all(food in values for food in foods):
            return {food: values[food] for food in foods}

        if all(position in values for position in range(len(foods))):
            return {
                food: values[position]
                for position, food in enumerate(foods)
            }

        if all(position in values for position in range(1, len(foods) + 1)):
            return {
                food: values[position]
                for position, food in enumerate(foods, start=1)
            }

        raise ValueError(
            f"{parameter_name} must use food names, zero-based integer keys, "
            "or one-based integer keys."
        )

    if isinstance(values, (str, bytes)):
        raise TypeError(f"{parameter_name} must be a sequence or mapping.")

    sequence = list(values)
    if len(sequence) != len(foods):
        raise ValueError(
            f"{parameter_name} must contain exactly {len(foods)} entries."
        )

    return dict(zip(foods, sequence))


def solve(params):
    foods = tuple(f"Food_{position}" for position in range(1, 6))

    protein_values = _normalize_food_values(
        params["protein_content"], foods, "protein_content"
    )
    carb_values = _normalize_food_values(
        params["carb_content"], foods, "carb_content"
    )
    calorie_values = _normalize_food_values(
        params["calorie_content"], foods, "calorie_content"
    )
    cost_values = _normalize_food_values(
        params["food_cost"], foods, "food_cost"
    )

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein_content = pyo.Param(
        model.foods, initialize=protein_values
    )
    model.carb_content = pyo.Param(
        model.foods, initialize=carb_values
    )
    model.calorie_content = pyo.Param(
        model.foods, initialize=calorie_values
    )
    model.food_cost = pyo.Param(
        model.foods, initialize=cost_values
    )

    model.protein_target = pyo.Param(initialize=params["protein_target"])
    model.carb_target = pyo.Param(initialize=params["carb_target"])
    model.calorie_target = pyo.Param(initialize=params["calorie_target"])

    model.portions = pyo.Var(
        model.foods, domain=pyo.NonNegativeIntegers
    )

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein_content[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_target
    )
    model.carb_requirement = pyo.Constraint(
        expr=sum(
            model.carb_content[food] * model.portions[food]
            for food in model.foods
        ) >= model.carb_target
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.calorie_content[food] * model.portions[food]
            for food in model.foods
        ) >= model.calorie_target
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.food_cost[food] * model.portions[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}