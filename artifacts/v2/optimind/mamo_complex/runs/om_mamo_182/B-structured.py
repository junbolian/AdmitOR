# IR: {"sets":{"foods":["bread","milk","fish","potato"]},"params":{"protein_content":"indexed by food","carb_content":"indexed by food","calorie_content":"indexed by food","cost_per_unit":"indexed by food","protein_requirement":"scalar","carb_requirement":"scalar","calorie_requirement":"scalar"},"variables":{"quantity[food]":"nonnegative continuous"},"constraints":["sum(protein_content[f]*quantity[f] for f in foods) >= protein_requirement","sum(carb_content[f]*quantity[f] for f in foods) >= carb_requirement","sum(calorie_content[f]*quantity[f] for f in foods) >= calorie_requirement"],"objective":"minimize sum(cost_per_unit[f]*quantity[f] for f in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Food inputs may be mappings keyed by food or sequences in food order."""
    foods = ("bread", "milk", "fish", "potato")

    def food_values(values):
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
    model.cost_per_unit = pyo.Param(
        model.foods, initialize=food_values(params["cost_per_unit"])
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
            model.cost_per_unit[food] * model.quantity[food]
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}