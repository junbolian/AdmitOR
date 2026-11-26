# IR: {"sets":{"foods":["bread","milk","fish","potato"]},"params":{"protein":{"bread":"protein_bread","milk":"protein_milk","fish":"protein_fish","potato":"protein_potato"},"carb":{"bread":"carb_bread","milk":"carb_milk","fish":"carb_fish","potato":"carb_potato"},"cal":{"bread":"cal_bread","milk":"cal_milk","fish":"cal_fish","potato":"cal_potato"},"cost":{"bread":"cost_bread","milk":"cost_milk","fish":"cost_fish","potato":"cost_potato"},"req_protein":"req_protein","req_carb":"req_carb","req_cal":"req_cal"},"variables":{"quantity[food]":"nonnegative continuous"},"constraints":["sum(protein[food]*quantity[food] for food in foods) >= req_protein","sum(carb[food]*quantity[food] for food in foods) >= req_carb","sum(cal[food]*quantity[food] for food in foods) >= req_cal"],"objective":"minimize sum(cost[food]*quantity[food] for food in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["bread", "milk", "fish", "potato"],
        ordered=True,
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
    model.carb = pyo.Param(
        model.foods,
        initialize={
            "bread": params["carb_bread"],
            "milk": params["carb_milk"],
            "fish": params["carb_fish"],
            "potato": params["carb_potato"],
        },
    )
    model.cal = pyo.Param(
        model.foods,
        initialize={
            "bread": params["cal_bread"],
            "milk": params["cal_milk"],
            "fish": params["cal_fish"],
            "potato": params["cal_potato"],
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

    model.req_protein = pyo.Param(initialize=params["req_protein"])
    model.req_carb = pyo.Param(initialize=params["req_carb"])
    model.req_cal = pyo.Param(initialize=params["req_cal"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food]
            for food in model.foods
        ) >= model.req_protein
    )
    model.carb_requirement = pyo.Constraint(
        expr=sum(
            model.carb[food] * model.quantity[food]
            for food in model.foods
        ) >= model.req_carb
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.cal[food] * model.quantity[food]
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
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" not in str(exc):
            raise
        return {"objective": None, "status": "no_feasible_solution"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}