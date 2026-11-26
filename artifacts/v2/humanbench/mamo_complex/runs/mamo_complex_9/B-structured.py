# IR: {"sets":{"foods":["Chicken","Rice","Broccoli","Tofu","Beans"]},"params":{"protein_content":"real[foods], input order","carb_content":"real[foods], input order","calorie_content":"real[foods], input order","cost":"real[foods], input order","protein_requirement":"real","carb_requirement":"real","calorie_requirement":"real"},"variables":{"quantity[foods]":"continuous, nonnegative"},"constraints":["sum(protein_content[f]*quantity[f] for f in foods) >= protein_requirement","sum(carb_content[f]*quantity[f] for f in foods) >= carb_requirement","sum(calorie_content[f]*quantity[f] for f in foods) >= calorie_requirement"],"objective":"minimize sum(cost[f]*quantity[f] for f in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("Chicken", "Rice", "Broccoli", "Tofu", "Beans")

    protein_content = params["protein_content"]
    carb_content = params["carb_content"]
    calorie_content = params["calorie_content"]
    cost = params["cost"]
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein_content = pyo.Param(
        model.foods,
        initialize={food: protein_content[idx] for idx, food in enumerate(foods)},
        within=pyo.Reals,
    )
    model.carb_content = pyo.Param(
        model.foods,
        initialize={food: carb_content[idx] for idx, food in enumerate(foods)},
        within=pyo.Reals,
    )
    model.calorie_content = pyo.Param(
        model.foods,
        initialize={food: calorie_content[idx] for idx, food in enumerate(foods)},
        within=pyo.Reals,
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={food: cost[idx] for idx, food in enumerate(foods)},
        within=pyo.Reals,
    )
    model.protein_requirement = pyo.Param(
        initialize=protein_requirement, within=pyo.Reals
    )
    model.carb_requirement = pyo.Param(
        initialize=carb_requirement, within=pyo.Reals
    )
    model.calorie_requirement = pyo.Param(
        initialize=calorie_requirement, within=pyo.Reals
    )

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_requirement
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calorie_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calorie_requirement
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
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}