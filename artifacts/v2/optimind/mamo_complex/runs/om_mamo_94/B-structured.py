# IR: {"sets":{"foods":["Chicken","Rice","Eggs","Beans","Spinach","Corn","Beef","Broccoli"]},"params":{"cost":"real[foods]","protein":"nonnegative_real[foods]","carbs":"nonnegative_real[foods]","calories":"nonnegative_real[foods]","protein_req":"nonnegative_real","carb_req":"nonnegative_real","calorie_req":"nonnegative_real"},"variables":{"portions":"nonnegative_integer[foods]"},"constraints":["sum(protein[f]*portions[f] for f in foods) >= protein_req","sum(carbs[f]*portions[f] for f in foods) >= carb_req","sum(calories[f]*portions[f] for f in foods) >= calorie_req"],"objective":"minimize sum(cost[f]*portions[f] for f in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Indexed inputs accept food-name mappings or sequences in foods order."""
    foods = (
        "Chicken",
        "Rice",
        "Eggs",
        "Beans",
        "Spinach",
        "Corn",
        "Beef",
        "Broccoli",
    )

    def indexed_data(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.cost = pyo.Param(
        model.foods,
        initialize=indexed_data(params["cost"]),
        within=pyo.Reals,
    )
    model.protein = pyo.Param(
        model.foods,
        initialize=indexed_data(params["protein"]),
        within=pyo.NonNegativeReals,
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize=indexed_data(params["carbs"]),
        within=pyo.NonNegativeReals,
    )
    model.calories = pyo.Param(
        model.foods,
        initialize=indexed_data(params["calories"]),
        within=pyo.NonNegativeReals,
    )
    model.protein_req = pyo.Param(
        initialize=params["protein_req"],
        within=pyo.NonNegativeReals,
    )
    model.carb_req = pyo.Param(
        initialize=params["carb_req"],
        within=pyo.NonNegativeReals,
    )
    model.calorie_req = pyo.Param(
        initialize=params["calorie_req"],
        within=pyo.NonNegativeReals,
    )

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_req
    )
    model.carbohydrate_requirement = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.portions[food]
            for food in model.foods
        ) >= model.carb_req
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.portions[food]
            for food in model.foods
        ) >= model.calorie_req
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.portions[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no solution is available to load.
        # Success is determined below solely by objective retrieval.
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}