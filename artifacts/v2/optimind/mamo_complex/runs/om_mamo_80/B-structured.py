# IR: {"sets":{"foods":["chicken","rice","tofu","spinach","almonds","salmon"]},"params":{"costs":"cost per serving, indexed by foods","protein":"protein per serving, indexed by foods","carbs":"carbohydrates per serving, indexed by foods","calories":"calories per serving, indexed by foods","req_protein":"minimum daily protein","req_carbs":"minimum daily carbohydrates","req_calories":"minimum daily calories"},"variables":{"servings[food]":"NonNegativeIntegers"},"constraints":["sum(protein[food]*servings[food] for food in foods) >= req_protein","sum(carbs[food]*servings[food] for food in foods) >= req_carbs","sum(calories[food]*servings[food] for food in foods) >= req_calories"],"objective":"minimize sum(costs[food]*servings[food] for food in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Indexed inputs may be food-keyed mappings or sequences in foods order."""
    foods = ("chicken", "rice", "tofu", "spinach", "almonds", "salmon")

    def indexed_data(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each indexed parameter must contain six values.")
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.costs = pyo.Param(
        model.foods, initialize=indexed_data(params["costs"])
    )
    model.protein = pyo.Param(
        model.foods, initialize=indexed_data(params["protein"])
    )
    model.carbs = pyo.Param(
        model.foods, initialize=indexed_data(params["carbs"])
    )
    model.calories = pyo.Param(
        model.foods, initialize=indexed_data(params["calories"])
    )
    model.req_protein = pyo.Param(initialize=params["req_protein"])
    model.req_carbs = pyo.Param(initialize=params["req_carbs"])
    model.req_calories = pyo.Param(initialize=params["req_calories"])

    model.servings = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.servings[food]
            for food in model.foods
        ) >= model.req_protein
    )
    model.carbs_requirement = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.servings[food]
            for food in model.foods
        ) >= model.req_carbs
    )
    model.calories_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.servings[food]
            for food in model.foods
        ) >= model.req_calories
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[food] * model.servings[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}