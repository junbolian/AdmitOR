# IR: {"sets":{"F":[0,1,2,3],"food_order":["brownie","ice_cream","cola","cheesecake"]},"params":{"calories_per_food":"array indexed by F","chocolate_per_food":"array indexed by F","sugar_per_food":"array indexed by F","fat_per_food":"array indexed by F","cost_per_food":"array indexed by F, cents per portion","min_calories":"scalar","min_chocolate":"scalar","min_sugar":"scalar","min_fat":"scalar"},"variables":{"portions[i]":"nonnegative integer for i in F"},"constraints":["sum(calories_per_food[i]*portions[i] for i in F) >= min_calories","sum(chocolate_per_food[i]*portions[i] for i in F) >= min_chocolate","sum(sugar_per_food[i]*portions[i] for i in F) >= min_sugar","sum(fat_per_food[i]*portions[i] for i in F) >= min_fat"],"objective":"minimize sum(cost_per_food[i]*portions[i] for i in F)/100, in dollars"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Food coefficient arrays follow the order specified in the IR."""
    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=range(4), ordered=True)

    model.calories = pyo.Param(
        model.foods,
        initialize={i: params["calories_per_food"][i] for i in range(4)},
        within=pyo.Reals,
    )
    model.chocolate = pyo.Param(
        model.foods,
        initialize={i: params["chocolate_per_food"][i] for i in range(4)},
        within=pyo.Reals,
    )
    model.sugar = pyo.Param(
        model.foods,
        initialize={i: params["sugar_per_food"][i] for i in range(4)},
        within=pyo.Reals,
    )
    model.fat = pyo.Param(
        model.foods,
        initialize={i: params["fat_per_food"][i] for i in range(4)},
        within=pyo.Reals,
    )
    model.unit_cost_cents = pyo.Param(
        model.foods,
        initialize={i: params["cost_per_food"][i] for i in range(4)},
        within=pyo.Reals,
    )

    model.required_calories = pyo.Param(
        initialize=params["min_calories"], within=pyo.Reals
    )
    model.required_chocolate = pyo.Param(
        initialize=params["min_chocolate"], within=pyo.Reals
    )
    model.required_sugar = pyo.Param(
        initialize=params["min_sugar"], within=pyo.Reals
    )
    model.required_fat = pyo.Param(
        initialize=params["min_fat"], within=pyo.Reals
    )

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.calorie_requirement = pyo.Constraint(
        expr=sum(model.calories[i] * model.portions[i] for i in model.foods)
        >= model.required_calories
    )
    model.chocolate_requirement = pyo.Constraint(
        expr=sum(model.chocolate[i] * model.portions[i] for i in model.foods)
        >= model.required_chocolate
    )
    model.sugar_requirement = pyo.Constraint(
        expr=sum(model.sugar[i] * model.portions[i] for i in model.foods)
        >= model.required_sugar
    )
    model.fat_requirement = pyo.Constraint(
        expr=sum(model.fat[i] * model.portions[i] for i in model.foods)
        >= model.required_fat
    )

    # Unit conversion: 100 cents per dollar.
    model.total_cost_dollars = pyo.Objective(
        expr=sum(
            model.unit_cost_cents[i] * model.portions[i]
            for i in model.foods
        ) / 100,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPSI raises RuntimeError when no feasible solution can be loaded.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost_dollars))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}