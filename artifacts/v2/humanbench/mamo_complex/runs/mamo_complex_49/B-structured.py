# IR: {"sets":{"foods":"0..8, ordered Chicken Breast, Tofu, Brown Rice, Salmon, Greek Yogurt, Steak, Avocado, Eggs, Quinoa"},"params":{"cost":"indexed by foods","protein":"indexed by foods","carbs":"indexed by foods","calories":"indexed by foods","protein_req":"scalar","carb_req":"scalar","calorie_req":"scalar"},"variables":{"quantity[i]":"continuous, nonnegative for each food i"},"constraints":["sum(protein[i]*quantity[i] for i in foods) >= protein_req","sum(carbs[i]*quantity[i] for i in foods) >= carb_req","sum(calories[i]*quantity[i] for i in foods) >= calorie_req"],"objective":"minimize sum(cost[i]*quantity[i] for i in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 8)

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

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[i] * model.quantity[i] for i in model.foods
        ) >= model.protein_req
    )
    model.carbohydrate_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[i] * model.quantity[i] for i in model.foods
        ) >= model.carb_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories[i] * model.quantity[i] for i in model.foods
        ) >= model.calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i] * model.quantity[i] for i in model.foods),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}