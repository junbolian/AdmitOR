# IR: {"sets":{"foods":["bread","milk","fish","potato"]},"params":{"protein":["protein_bread","protein_milk","protein_fish","protein_potato"],"carbs":["carbs_bread","carbs_milk","carbs_fish","carbs_potato"],"calories":["calories_bread","calories_milk","calories_fish","calories_potato"],"cost":["cost_bread","cost_milk","cost_fish","cost_potato"],"requirements":["protein_req","carbs_req","calories_req"]},"variables":{"quantity[foods]":"nonnegative continuous"},"constraints":["sum(protein[f]*quantity[f] for f in foods) >= protein_req","sum(carbs[f]*quantity[f] for f in foods) >= carbs_req","sum(calories[f]*quantity[f] for f in foods) >= calories_req"],"objective":"minimize sum(cost[f]*quantity[f] for f in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["bread", "milk", "fish", "potato"], ordered=True
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "bread": params["protein_bread"],
            "milk": params["protein_milk"],
            "fish": params["protein_fish"],
            "potato": params["protein_potato"],
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "bread": params["carbs_bread"],
            "milk": params["carbs_milk"],
            "fish": params["carbs_fish"],
            "potato": params["carbs_potato"],
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "bread": params["calories_bread"],
            "milk": params["calories_milk"],
            "fish": params["calories_fish"],
            "potato": params["calories_potato"],
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            "bread": params["cost_bread"],
            "milk": params["cost_milk"],
            "fish": params["cost_fish"],
            "potato": params["cost_potato"],
        },
    )

    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carbs_req = pyo.Param(initialize=params["carbs_req"])
    model.calories_req = pyo.Param(initialize=params["calories_req"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_req
    )
    model.carbs_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carbs_req
    )
    model.calories_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calories_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.quantity[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": failure_reason}

    # Preserve the exact objective required by the return contract;
    # nearest-dollar presentation can use round(result["objective"]).
    return {"objective": obj_val, "status": "optimal"}