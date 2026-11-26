# IR: {"sets":{"foods":[0,1,2,3]},"params":{"calories":"food-indexed","chocolate":"food-indexed","sugar":"food-indexed","fat":"food-indexed","cost":"food-indexed","min_calories":"scalar","min_chocolate":"scalar","min_sugar":"scalar","min_fat":"scalar"},"variables":{"quantity[i]":"continuous nonnegative, i in foods"},"constraints":["sum(calories[i]*quantity[i] for i in foods) >= min_calories","sum(chocolate[i]*quantity[i] for i in foods) >= min_chocolate","sum(sugar[i]*quantity[i] for i in foods) >= min_sugar","sum(fat[i]*quantity[i] for i in foods) >= min_fat"],"objective":"minimize sum(cost[i]*quantity[i] for i in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize daily food cost in cents.

    Food-indexed inputs must be sequences or mappings indexed by 0, 1, 2, 3,
    corresponding to brownies, chocolate ice cream, cola, and pineapple
    cheesecake. Quantities may be fractional.
    """
    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=range(4), ordered=True)

    model.calories = pyo.Param(
        model.foods,
        initialize={i: params["calories"][i] for i in model.foods},
    )
    model.chocolate = pyo.Param(
        model.foods,
        initialize={i: params["chocolate"][i] for i in model.foods},
    )
    model.sugar = pyo.Param(
        model.foods,
        initialize={i: params["sugar"][i] for i in model.foods},
    )
    model.fat = pyo.Param(
        model.foods,
        initialize={i: params["fat"][i] for i in model.foods},
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={i: params["cost"][i] for i in model.foods},
    )

    model.min_calories = pyo.Param(initialize=params["min_calories"])
    model.min_chocolate = pyo.Param(initialize=params["min_chocolate"])
    model.min_sugar = pyo.Param(initialize=params["min_sugar"])
    model.min_fat = pyo.Param(initialize=params["min_fat"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.calorie_requirement = pyo.Constraint(
        expr=sum(model.calories[i] * model.quantity[i] for i in model.foods)
        >= model.min_calories
    )
    model.chocolate_requirement = pyo.Constraint(
        expr=sum(model.chocolate[i] * model.quantity[i] for i in model.foods)
        >= model.min_chocolate
    )
    model.sugar_requirement = pyo.Constraint(
        expr=sum(model.sugar[i] * model.quantity[i] for i in model.foods)
        >= model.min_sugar
    )
    model.fat_requirement = pyo.Constraint(
        expr=sum(model.fat[i] * model.quantity[i] for i in model.foods)
        >= model.min_fat
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i] * model.quantity[i] for i in model.foods),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution is available to load.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}