# IR: {"sets":{"foods":["bread","milk","fish","potato"]},"params":["protein_bread","carb_bread","calorie_bread","cost_bread","protein_milk","carb_milk","calorie_milk","cost_milk","protein_fish","carb_fish","calorie_fish","cost_fish","protein_potato","carb_potato","calorie_potato","cost_potato","req_protein","req_carbs","req_calories"],"variables":{"quantity[foods]":"nonnegative continuous"},"constraints":["sum(protein[f]*quantity[f] for f in foods) >= req_protein","sum(carbs[f]*quantity[f] for f in foods) >= req_carbs","sum(calories[f]*quantity[f] for f in foods) >= req_calories"],"objective":"minimize sum(cost[f]*quantity[f] for f in foods)","reporting":"return the optimal cost rounded to the nearest dollar"}
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
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "bread": params["carb_bread"],
            "milk": params["carb_milk"],
            "fish": params["carb_fish"],
            "potato": params["carb_potato"],
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "bread": params["calorie_bread"],
            "milk": params["calorie_milk"],
            "fish": params["calorie_fish"],
            "potato": params["calorie_potato"],
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
    model.req_carbs = pyo.Param(initialize=params["req_carbs"])
    model.req_calories = pyo.Param(initialize=params["req_calories"])

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
        ) >= model.req_calories
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
        # Appsi raises this when it cannot load a feasible solution.
        if "feasible solution" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}