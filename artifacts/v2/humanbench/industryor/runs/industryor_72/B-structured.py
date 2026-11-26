# IR: {"sets":{"fruits":["apples","pears","oranges","lemons"]},"params":["profit_apples","profit_pears","profit_oranges","profit_lemons","total_land","apples_vs_pears_ratio","apples_vs_lemons_ratio","oranges_vs_lemons_ratio","max_fruit_types"],"variables":{"acres[fruits]":"NonNegativeReals","grown[fruits]":"Binary"},"constraints":["sum(acres[f] for f in fruits) <= total_land","acres[apples] >= apples_vs_pears_ratio * acres[pears]","acres[apples] >= apples_vs_lemons_ratio * acres[lemons]","acres[oranges] == oranges_vs_lemons_ratio * acres[lemons]","acres[f] <= total_land * grown[f] for f in fruits","sum(grown[f] for f in fruits) <= max_fruit_types"],"objective":"maximize sum(profit[f] * acres[f] for f in fruits)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.fruits = pyo.Set(
        initialize=["apples", "pears", "oranges", "lemons"],
        ordered=True,
    )

    model.profit = pyo.Param(
        model.fruits,
        initialize={
            "apples": params["profit_apples"],
            "pears": params["profit_pears"],
            "oranges": params["profit_oranges"],
            "lemons": params["profit_lemons"],
        },
    )
    model.total_land = pyo.Param(initialize=params["total_land"])
    model.apples_vs_pears_ratio = pyo.Param(
        initialize=params["apples_vs_pears_ratio"]
    )
    model.apples_vs_lemons_ratio = pyo.Param(
        initialize=params["apples_vs_lemons_ratio"]
    )
    model.oranges_vs_lemons_ratio = pyo.Param(
        initialize=params["oranges_vs_lemons_ratio"]
    )
    model.max_fruit_types = pyo.Param(
        initialize=params["max_fruit_types"]
    )

    model.acres = pyo.Var(model.fruits, domain=pyo.NonNegativeReals)
    model.grown = pyo.Var(model.fruits, domain=pyo.Binary)

    model.land_limit = pyo.Constraint(
        expr=sum(model.acres[fruit] for fruit in model.fruits)
        <= model.total_land
    )
    model.apple_pear_requirement = pyo.Constraint(
        expr=model.acres["apples"]
        >= model.apples_vs_pears_ratio * model.acres["pears"]
    )
    model.apple_lemon_requirement = pyo.Constraint(
        expr=model.acres["apples"]
        >= model.apples_vs_lemons_ratio * model.acres["lemons"]
    )
    model.orange_lemon_requirement = pyo.Constraint(
        expr=model.acres["oranges"]
        == model.oranges_vs_lemons_ratio * model.acres["lemons"]
    )

    def acreage_link_rule(instance, fruit):
        return (
            instance.acres[fruit]
            <= instance.total_land * instance.grown[fruit]
        )

    model.acreage_link = pyo.Constraint(
        model.fruits, rule=acreage_link_rule
    )
    model.fruit_type_limit = pyo.Constraint(
        expr=sum(model.grown[fruit] for fruit in model.fruits)
        <= model.max_fruit_types
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[fruit] * model.acres[fruit]
            for fruit in model.fruits
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}