# IR: {"sets":{"foods":["Food_1","Food_2","Food_3","Food_4"]},"params":{"protein_content":"foods -> grams/unit","carb_content":"foods -> grams/unit","calorie_content":"foods -> kcal/unit","cost":"foods -> cost/unit","protein_requirement":"scalar","carb_requirement":"scalar","calorie_requirement":"scalar"},"variables":{"quantity":{"index":"foods","type":"nonnegative continuous"}},"constraints":["sum(protein_content[f]*quantity[f] for f in foods) >= protein_requirement","sum(carb_content[f]*quantity[f] for f in foods) >= carb_requirement","sum(calorie_content[f]*quantity[f] for f in foods) >= calorie_requirement"],"objective":{"sense":"minimize","expression":"sum(cost[f]*quantity[f] for f in foods)"}}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Food data may be mappings keyed by Food_1..Food_4 or ordered sequences."""
    foods = ("Food_1", "Food_2", "Food_3", "Food_4")

    def food_data(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each food parameter must contain four values.")
        return {food: values[position] for position, food in enumerate(foods)}

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

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_requirement
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calorie_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calorie_requirement
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
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}