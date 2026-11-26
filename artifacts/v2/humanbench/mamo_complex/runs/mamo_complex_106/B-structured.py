# IR: {"sets":{"foods":["chicken","rice","apples","cheese","tofu"]},"params":["protein_chicken","carb_chicken","cal_chicken","cost_chicken","protein_rice","carb_rice","cal_rice","cost_rice","protein_apples","carb_apples","cal_apples","cost_apples","protein_cheese","carb_cheese","cal_cheese","cost_cheese","protein_tofu","carb_tofu","cal_tofu","cost_tofu","protein_req","carb_req","cal_req"],"variables":{"quantity[food]":"nonnegative continuous"},"constraints":["sum(protein[food]*quantity[food] for food in foods) >= protein_req","sum(carb[food]*quantity[food] for food in foods) >= carb_req","sum(cal[food]*quantity[food] for food in foods) >= cal_req"],"objective":"minimize sum(cost[food]*quantity[food] for food in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["chicken", "rice", "apples", "cheese", "tofu"],
        ordered=True,
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["protein_chicken"],
            "rice": params["protein_rice"],
            "apples": params["protein_apples"],
            "cheese": params["protein_cheese"],
            "tofu": params["protein_tofu"],
        },
    )
    model.carb = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["carb_chicken"],
            "rice": params["carb_rice"],
            "apples": params["carb_apples"],
            "cheese": params["carb_cheese"],
            "tofu": params["carb_tofu"],
        },
    )
    model.cal = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cal_chicken"],
            "rice": params["cal_rice"],
            "apples": params["cal_apples"],
            "cheese": params["cal_cheese"],
            "tofu": params["cal_tofu"],
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cost_chicken"],
            "rice": params["cost_rice"],
            "apples": params["cost_apples"],
            "cheese": params["cost_cheese"],
            "tofu": params["cost_tofu"],
        },
    )

    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carb_req = pyo.Param(initialize=params["carb_req"])
    model.cal_req = pyo.Param(initialize=params["cal_req"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_req
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carb_req
    )
    model.cal_minimum = pyo.Constraint(
        expr=sum(
            model.cal[food] * model.quantity[food]
            for food in model.foods
        ) >= model.cal_req
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}