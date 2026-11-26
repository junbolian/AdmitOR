# IR: {"sets":{"fruits":["apples","pears","oranges","lemons"]},"params":["profit_apples","profit_pears","profit_oranges","profit_lemons","total_land","apple_vs_pear_ratio","apple_vs_lemon_ratio","orange_vs_lemon_ratio","max_fruit_types"],"variables":{"acres[fruits]":"NonNegativeReals","selected[fruits]":"Binary"},"constraints":["sum(acres[f] for f in fruits) <= total_land","acres[f] <= total_land * selected[f] for each f","sum(selected[f] for f in fruits) <= max_fruit_types","acres[apples] >= apple_vs_pear_ratio * acres[pears]","acres[apples] >= apple_vs_lemon_ratio * acres[lemons]","acres[oranges] >= orange_vs_lemon_ratio * acres[lemons]","acres[oranges] - orange_vs_lemon_ratio * acres[lemons] <= total_land * (1 - selected[lemons])"],"objective":"maximize sum(profit[f] * acres[f] for f in fruits)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profits = {
        "apples": params["profit_apples"],
        "pears": params["profit_pears"],
        "oranges": params["profit_oranges"],
        "lemons": params["profit_lemons"],
    }
    total_land = params["total_land"]
    apple_vs_pear_ratio = params["apple_vs_pear_ratio"]
    apple_vs_lemon_ratio = params["apple_vs_lemon_ratio"]
    orange_vs_lemon_ratio = params["orange_vs_lemon_ratio"]
    max_fruit_types = params["max_fruit_types"]

    model = pyo.ConcreteModel()
    model.fruits = pyo.Set(
        initialize=["apples", "pears", "oranges", "lemons"],
        ordered=True,
    )

    model.acres = pyo.Var(model.fruits, domain=pyo.NonNegativeReals)
    model.selected = pyo.Var(model.fruits, domain=pyo.Binary)

    model.land_limit = pyo.Constraint(
        expr=sum(model.acres[fruit] for fruit in model.fruits) <= total_land
    )

    def acreage_link_rule(instance, fruit):
        return (
            instance.acres[fruit]
            <= total_land * instance.selected[fruit]
        )

    model.acreage_link = pyo.Constraint(
        model.fruits, rule=acreage_link_rule
    )

    model.fruit_type_limit = pyo.Constraint(
        expr=sum(model.selected[fruit] for fruit in model.fruits)
        <= max_fruit_types
    )

    model.apple_pear_requirement = pyo.Constraint(
        expr=model.acres["apples"]
        >= apple_vs_pear_ratio * model.acres["pears"]
    )

    model.apple_lemon_requirement = pyo.Constraint(
        expr=model.acres["apples"]
        >= apple_vs_lemon_ratio * model.acres["lemons"]
    )

    # When lemons have positive acreage, their selection binary must be 1,
    # and these two inequalities enforce the required equality.
    # When lemons are absent, selecting their binary as 0 leaves oranges
    # unrestricted except for the existing land and fruit-count limits.
    model.orange_lemon_lower = pyo.Constraint(
        expr=model.acres["oranges"]
        >= orange_vs_lemon_ratio * model.acres["lemons"]
    )

    model.orange_lemon_upper = pyo.Constraint(
        expr=(
            model.acres["oranges"]
            - orange_vs_lemon_ratio * model.acres["lemons"]
            <= total_land * (1 - model.selected["lemons"])
        )
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            profits[fruit] * model.acres[fruit]
            for fruit in model.fruits
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}