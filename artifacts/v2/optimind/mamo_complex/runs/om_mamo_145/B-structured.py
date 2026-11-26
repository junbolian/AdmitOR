# IR: {"sets":{"foods":["eggs","rice","chicken","broccoli"]},"params":{"protein":["protein_eggs","protein_rice","protein_chicken","protein_broccoli"],"carb":["carb_eggs","carb_rice","carb_chicken","carb_broccoli"],"cal":["cal_eggs","cal_rice","cal_chicken","cal_broccoli"],"cost":["cost_eggs","cost_rice","cost_chicken","cost_broccoli"],"requirements":["protein_req","carb_req","cal_req"]},"variables":{"portions[foods]":"NonNegativeIntegers"},"constraints":["sum(protein[f]*portions[f] for f in foods) >= protein_req","sum(carb[f]*portions[f] for f in foods) >= carb_req","sum(cal[f]*portions[f] for f in foods) >= cal_req"],"objective":{"sense":"minimize","expression":"sum(cost[f]*portions[f] for f in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["eggs", "rice", "chicken", "broccoli"],
        ordered=True,
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
    model.carb = pyo.Param(
        model.foods,
        initialize={
            "eggs": params["carb_eggs"],
            "rice": params["carb_rice"],
            "chicken": params["carb_chicken"],
            "broccoli": params["carb_broccoli"],
        },
    )
    model.cal = pyo.Param(
        model.foods,
        initialize={
            "eggs": params["cal_eggs"],
            "rice": params["cal_rice"],
            "chicken": params["cal_chicken"],
            "broccoli": params["cal_broccoli"],
        },
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

    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carb_req = pyo.Param(initialize=params["carb_req"])
    model.cal_req = pyo.Param(initialize=params["cal_req"])

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_req
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb[food] * model.portions[food]
            for food in model.foods
        ) >= model.carb_req
    )
    model.cal_minimum = pyo.Constraint(
        expr=sum(
            model.cal[food] * model.portions[food]
            for food in model.foods
        ) >= model.cal_req
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}