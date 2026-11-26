# IR: {"sets":{"foods":["chicken","oats","tofu","rice","beef","salmon"],"nutrients":["protein","carbs","calories"]},"params":["protein_chicken","protein_oats","protein_tofu","protein_rice","protein_beef","protein_salmon","carbs_chicken","carbs_oats","carbs_tofu","carbs_rice","carbs_beef","carbs_salmon","calories_chicken","calories_oats","calories_tofu","calories_rice","calories_beef","calories_salmon","cost_chicken","cost_oats","cost_tofu","cost_rice","cost_beef","cost_salmon","protein_target","carb_target","calorie_target"],"variables":{"portions[food]":"nonnegative integer"},"constraints":["For each nutrient: sum(nutrient_content[nutrient,food]*portions[food] for food in foods) >= target[nutrient]"],"objective":"minimize sum(cost[food]*portions[food] for food in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("chicken", "oats", "tofu", "rice", "beef", "salmon")
    nutrients = ("protein", "carbs", "calories")

    nutrient_content = {
        ("protein", "chicken"): params["protein_chicken"],
        ("protein", "oats"): params["protein_oats"],
        ("protein", "tofu"): params["protein_tofu"],
        ("protein", "rice"): params["protein_rice"],
        ("protein", "beef"): params["protein_beef"],
        ("protein", "salmon"): params["protein_salmon"],
        ("carbs", "chicken"): params["carbs_chicken"],
        ("carbs", "oats"): params["carbs_oats"],
        ("carbs", "tofu"): params["carbs_tofu"],
        ("carbs", "rice"): params["carbs_rice"],
        ("carbs", "beef"): params["carbs_beef"],
        ("carbs", "salmon"): params["carbs_salmon"],
        ("calories", "chicken"): params["calories_chicken"],
        ("calories", "oats"): params["calories_oats"],
        ("calories", "tofu"): params["calories_tofu"],
        ("calories", "rice"): params["calories_rice"],
        ("calories", "beef"): params["calories_beef"],
        ("calories", "salmon"): params["calories_salmon"],
    }
    costs = {
        "chicken": params["cost_chicken"],
        "oats": params["cost_oats"],
        "tofu": params["cost_tofu"],
        "rice": params["cost_rice"],
        "beef": params["cost_beef"],
        "salmon": params["cost_salmon"],
    }
    targets = {
        "protein": params["protein_target"],
        "carbs": params["carb_target"],
        "calories": params["calorie_target"],
    }

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)
    model.nutrients = pyo.Set(initialize=nutrients, ordered=True)

    model.nutrient_content = pyo.Param(
        model.nutrients,
        model.foods,
        initialize=nutrient_content,
    )
    model.cost = pyo.Param(model.foods, initialize=costs)
    model.target = pyo.Param(model.nutrients, initialize=targets)

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    def nutrient_requirement_rule(instance, nutrient):
        return sum(
            instance.nutrient_content[nutrient, food] * instance.portions[food]
            for food in instance.foods
        ) >= instance.target[nutrient]

    model.nutrient_requirements = pyo.Constraint(
        model.nutrients,
        rule=nutrient_requirement_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(model.cost[food] * model.portions[food] for food in model.foods),
        sense=pyo.minimize,
    )

    # APPsi raises RuntimeError when no feasible solution can be loaded.
    # Success is determined exclusively by objective-value retrieval below.
    solve_failure = None
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failure = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": solve_failure or "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}