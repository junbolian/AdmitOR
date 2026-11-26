# IR: {"sets":{"foods":["chicken","pasta","apples","tuna","rice"],"nutrients":["protein","carbs","calories"]},"params":{"cost[f]":"params['cost_'+f]","content[n,f]":"params[n+'_'+f]","requirement[n]":"params[n+'_req']"},"variables":{"portions[f]":"nonnegative integer"},"constraints":["For each nutrient n: sum(content[n,f]*portions[f] for f in foods) >= requirement[n]"],"objective":"Minimize sum(cost[f]*portions[f] for f in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["chicken", "pasta", "apples", "tuna", "rice"],
        ordered=True,
    )
    model.nutrients = pyo.Set(
        initialize=["protein", "carbs", "calories"],
        ordered=True,
    )

    model.cost = pyo.Param(
        model.foods,
        initialize={
            food: params["cost_" + food]
            for food in model.foods
        },
    )
    model.content = pyo.Param(
        model.nutrients,
        model.foods,
        initialize={
            (nutrient, food): params[nutrient + "_" + food]
            for nutrient in model.nutrients
            for food in model.foods
        },
    )
    model.requirement = pyo.Param(
        model.nutrients,
        initialize={
            nutrient: params[nutrient + "_req"]
            for nutrient in model.nutrients
        },
    )

    model.portions = pyo.Var(
        model.foods,
        domain=pyo.NonNegativeIntegers,
    )

    def nutrient_minimum_rule(instance, nutrient):
        return (
            sum(
                instance.content[nutrient, food] * instance.portions[food]
                for food in instance.foods
            )
            >= instance.requirement[nutrient]
        )

    model.nutrient_minimum = pyo.Constraint(
        model.nutrients,
        rule=nutrient_minimum_rule,
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}