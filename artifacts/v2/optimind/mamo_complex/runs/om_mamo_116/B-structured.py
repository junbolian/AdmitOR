# IR: {"sets":{"F":[0,1,2,3,4,5,6]},"params":{"cost":"length-7 array","protein":"length-7 array","carbs":"length-7 array","calories":"length-7 array","protein_req":"scalar","carb_req":"scalar","calorie_req":"scalar"},"variables":{"portions[i]":"nonnegative integer, i in F"},"constraints":["sum(protein[i]*portions[i] for i in F) >= protein_req","sum(carbs[i]*portions[i] for i in F) >= carb_req","sum(calories[i]*portions[i] for i in F) >= calorie_req"],"objective":"minimize sum(cost[i]*portions[i] for i in F)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Array entries correspond to Food_1 through Food_7, respectively."""
    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 6)

    model.cost = pyo.Param(
        model.foods,
        initialize={i: params["cost"][i] for i in model.foods},
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={i: params["protein"][i] for i in model.foods},
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={i: params["carbs"][i] for i in model.foods},
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={i: params["calories"][i] for i in model.foods},
    )
    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carb_req = pyo.Param(initialize=params["carb_req"])
    model.calorie_req = pyo.Param(initialize=params["calorie_req"])

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_minimum = pyo.Constraint(
        expr=sum(model.protein[i] * model.portions[i] for i in model.foods)
        >= model.protein_req
    )
    model.carbohydrate_minimum = pyo.Constraint(
        expr=sum(model.carbs[i] * model.portions[i] for i in model.foods)
        >= model.carb_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(model.calories[i] * model.portions[i] for i in model.foods)
        >= model.calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i] * model.portions[i] for i in model.foods),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}