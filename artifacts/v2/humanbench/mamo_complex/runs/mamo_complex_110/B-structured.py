# IR: {"sets":{"foods":["eggs","rice","chicken","broccoli"]},"params":["cost_eggs","cost_rice","cost_chicken","cost_broccoli","protein_eggs","protein_rice","protein_chicken","protein_broccoli","carbs_eggs","carbs_rice","carbs_chicken","carbs_broccoli","cal_eggs","cal_rice","cal_chicken","cal_broccoli","req_protein","req_carbs","req_cal"],"variables":{"quantity[foods]":"nonnegative continuous"},"constraints":["sum(protein[f]*quantity[f] for f in foods) >= req_protein","sum(carbs[f]*quantity[f] for f in foods) >= req_carbs","sum(calories[f]*quantity[f] for f in foods) >= req_cal"],"objective":"minimize sum(cost[f]*quantity[f] for f in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["eggs", "rice", "chicken", "broccoli"],
        ordered=True,
    )

    model.cost = pyo.Param(
        model.foods,
        initialize={
            "eggs": params["cost_eggs"],
            "rice": params["cost_rice"],
            "chicken": params["cost_chicken"],
            "broccoli": params["cost_broccoli"],
        },
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={
            "eggs": params["protein_eggs"],
            "rice": params["protein_rice"],
            "chicken": params["protein_chicken"],
            "broccoli": params["protein_broccoli"],
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "eggs": params["carbs_eggs"],
            "rice": params["carbs_rice"],
            "chicken": params["carbs_chicken"],
            "broccoli": params["carbs_broccoli"],
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "eggs": params["cal_eggs"],
            "rice": params["cal_rice"],
            "chicken": params["cal_chicken"],
            "broccoli": params["cal_broccoli"],
        },
    )

    model.req_protein = pyo.Param(initialize=params["req_protein"])
    model.req_carbs = pyo.Param(initialize=params["req_carbs"])
    model.req_cal = pyo.Param(initialize=params["req_cal"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food]
            for food in model.foods
        ) >= model.req_protein
    )
    model.carbohydrate_requirement = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.quantity[food]
            for food in model.foods
        ) >= model.req_carbs
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food]
            for food in model.foods
        ) >= model.req_cal
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}