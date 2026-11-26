# IR: {"sets":{"foods":["chicken","rice","broccoli","tofu","beans"]},"params":{"cost[foods]":["cost_chicken","cost_rice","cost_broccoli","cost_tofu","cost_beans"],"protein[foods]":["protein_chicken","protein_rice","protein_broccoli","protein_tofu","protein_beans"],"carb[foods]":["carb_chicken","carb_rice","carb_broccoli","carb_tofu","carb_beans"],"calories[foods]":["cal_chicken","cal_rice","cal_broccoli","cal_tofu","cal_beans"],"req_protein":"req_protein","req_carb":"req_carb","req_cal":"req_cal"},"variables":{"portions[foods]":"nonnegative integer"},"constraints":["sum(protein[f]*portions[f] for f in foods) >= req_protein","sum(carb[f]*portions[f] for f in foods) >= req_carb","sum(calories[f]*portions[f] for f in foods) >= req_cal"],"objective":{"sense":"minimize","expression":"sum(cost[f]*portions[f] for f in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["chicken", "rice", "broccoli", "tofu", "beans"],
        ordered=True,
    )

    model.cost = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cost_chicken"],
            "rice": params["cost_rice"],
            "broccoli": params["cost_broccoli"],
            "tofu": params["cost_tofu"],
            "beans": params["cost_beans"],
        },
        within=pyo.Reals,
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["protein_chicken"],
            "rice": params["protein_rice"],
            "broccoli": params["protein_broccoli"],
            "tofu": params["protein_tofu"],
            "beans": params["protein_beans"],
        },
        within=pyo.Reals,
    )
    model.carb = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["carb_chicken"],
            "rice": params["carb_rice"],
            "broccoli": params["carb_broccoli"],
            "tofu": params["carb_tofu"],
            "beans": params["carb_beans"],
        },
        within=pyo.Reals,
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cal_chicken"],
            "rice": params["cal_rice"],
            "broccoli": params["cal_broccoli"],
            "tofu": params["cal_tofu"],
            "beans": params["cal_beans"],
        },
        within=pyo.Reals,
    )

    model.req_protein = pyo.Param(
        initialize=params["req_protein"], within=pyo.Reals
    )
    model.req_carb = pyo.Param(
        initialize=params["req_carb"], within=pyo.Reals
    )
    model.req_cal = pyo.Param(
        initialize=params["req_cal"], within=pyo.Reals
    )

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.req_protein
    )
    model.carb_requirement = pyo.Constraint(
        expr=sum(
            model.carb[food] * model.portions[food]
            for food in model.foods
        ) >= model.req_carb
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.portions[food]
            for food in model.foods
        ) >= model.req_cal
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
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}