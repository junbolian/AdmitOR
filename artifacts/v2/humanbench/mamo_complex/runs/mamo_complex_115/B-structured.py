# IR: {"sets":{"foods":["chicken","rice","tuna","beef","corn","whey"],"nutrients":["protein","carbs","calories"]},"params":{"nutrient_content[nutrient,food]":"params[nutrient + '_' + food]","unit_cost[food]":"params['cost_' + food]","minimum[nutrient]":"params['target_' + nutrient]"},"variables":{"quantity[food]":{"type":"continuous","lower_bound":0}},"constraints":["For each nutrient: sum(nutrient_content[nutrient,food] * quantity[food] for food in foods) >= minimum[nutrient]"],"objective":{"sense":"minimize","expression":"sum(unit_cost[food] * quantity[food] for food in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["chicken", "rice", "tuna", "beef", "corn", "whey"],
        ordered=True,
    )
    model.nutrients = pyo.Set(
        initialize=["protein", "carbs", "calories"],
        ordered=True,
    )

    nutrient_data = {
        ("protein", "chicken"): params["protein_chicken"],
        ("protein", "rice"): params["protein_rice"],
        ("protein", "tuna"): params["protein_tuna"],
        ("protein", "beef"): params["protein_beef"],
        ("protein", "corn"): params["protein_corn"],
        ("protein", "whey"): params["protein_whey"],
        ("carbs", "chicken"): params["carbs_chicken"],
        ("carbs", "rice"): params["carbs_rice"],
        ("carbs", "tuna"): params["carbs_tuna"],
        ("carbs", "beef"): params["carbs_beef"],
        ("carbs", "corn"): params["carbs_corn"],
        ("carbs", "whey"): params["carbs_whey"],
        ("calories", "chicken"): params["calories_chicken"],
        ("calories", "rice"): params["calories_rice"],
        ("calories", "tuna"): params["calories_tuna"],
        ("calories", "beef"): params["calories_beef"],
        ("calories", "corn"): params["calories_corn"],
        ("calories", "whey"): params["calories_whey"],
    }
    cost_data = {
        "chicken": params["cost_chicken"],
        "rice": params["cost_rice"],
        "tuna": params["cost_tuna"],
        "beef": params["cost_beef"],
        "corn": params["cost_corn"],
        "whey": params["cost_whey"],
    }
    minimum_data = {
        "protein": params["target_protein"],
        "carbs": params["target_carbs"],
        "calories": params["target_calories"],
    }

    model.nutrient_content = pyo.Param(
        model.nutrients,
        model.foods,
        initialize=nutrient_data,
        within=pyo.Reals,
    )
    model.unit_cost = pyo.Param(
        model.foods,
        initialize=cost_data,
        within=pyo.Reals,
    )
    model.minimum = pyo.Param(
        model.nutrients,
        initialize=minimum_data,
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    def nutrient_requirement_rule(instance, nutrient):
        return (
            sum(
                instance.nutrient_content[nutrient, food]
                * instance.quantity[food]
                for food in instance.foods
            )
            >= instance.minimum[nutrient]
        )

    model.nutrient_requirements = pyo.Constraint(
        model.nutrients,
        rule=nutrient_requirement_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[food] * model.quantity[food]
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