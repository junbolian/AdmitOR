# IR: {"sets":{"foods":[0,1,2,3,4,5]},"params":{"cost":"food-indexed costs","protein":"food-indexed protein grams","carbs":"food-indexed carbohydrate grams; informational only","calories":"food-indexed calories","protein_req_1":"first minimum daily protein","protein_req_2":"second minimum daily protein","calorie_req":"minimum daily calories"},"variables":{"portions[foods]":"nonnegative integer"},"constraints":["sum(protein[i]*portions[i] for i in foods) >= protein_req_1","sum(protein[i]*portions[i] for i in foods) >= protein_req_2","sum(calories[i]*portions[i] for i in foods) >= calorie_req"],"objective":"minimize sum(cost[i]*portions[i] for i in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Food data must be sequences or mappings indexed from 0 through 5.

    Both protein requirements are enforced as written. Carbohydrate data
    are retained, but no carbohydrate requirement is specified.
    """
    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 5)

    model.cost = pyo.Param(
        model.foods,
        initialize={food: params["cost"][food] for food in model.foods},
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={food: params["protein"][food] for food in model.foods},
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={food: params["carbs"][food] for food in model.foods},
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={food: params["calories"][food] for food in model.foods},
    )
    model.protein_req_1 = pyo.Param(initialize=params["protein_req_1"])
    model.protein_req_2 = pyo.Param(initialize=params["protein_req_2"])
    model.calorie_req = pyo.Param(initialize=params["calorie_req"])

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_minimum_1 = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_req_1
    )
    model.protein_minimum_2 = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_req_2
    )
    model.calorie_minimum = pyo.Constraint(
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

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}