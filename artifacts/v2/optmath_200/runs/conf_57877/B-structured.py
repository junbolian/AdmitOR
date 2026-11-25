# IR: {"sets":{"foods":"range(params['num_foods'])","nutrients":"range(params['num_nutrients'])"},"params":{"num_foods":"index-set size","num_nutrients":"index-set size","costs":"real[foods]","nutrient_min":"real[nutrients]","nutrient_max":"real[nutrients]","nutrient_coeffs":"real[nutrients,foods], nutrient-major"},"variables":{"quantity":{"type":"continuous","domain":"nonnegative","index":"foods"}},"constraints":["nutrient_min[n] <= sum(nutrient_coeffs[n,f]*quantity[f] for f in foods) <= nutrient_max[n] for n in nutrients"],"objective":{"sense":"minimize","expression":"sum(costs[f]*quantity[f] for f in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=range(params["num_foods"]),
        ordered=True,
    )
    model.nutrients = pyo.Set(
        initialize=range(params["num_nutrients"]),
        ordered=True,
    )

    model.costs = pyo.Param(
        model.foods,
        initialize=lambda mdl, food: params["costs"][food],
        within=pyo.Reals,
    )
    model.nutrient_min = pyo.Param(
        model.nutrients,
        initialize=lambda mdl, nutrient: params["nutrient_min"][nutrient],
        within=pyo.Reals,
    )
    model.nutrient_max = pyo.Param(
        model.nutrients,
        initialize=lambda mdl, nutrient: params["nutrient_max"][nutrient],
        within=pyo.Reals,
    )
    model.nutrient_coeffs = pyo.Param(
        model.nutrients,
        model.foods,
        initialize=lambda mdl, nutrient, food: (
            params["nutrient_coeffs"][nutrient][food]
        ),
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    def nutrient_bounds_rule(mdl, nutrient):
        intake = pyo.quicksum(
            mdl.nutrient_coeffs[nutrient, food] * mdl.quantity[food]
            for food in mdl.foods
        )
        return (
            mdl.nutrient_min[nutrient],
            intake,
            mdl.nutrient_max[nutrient],
        )

    model.nutrient_bounds = pyo.Constraint(
        model.nutrients,
        rule=nutrient_bounds_rule,
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.costs[food] * model.quantity[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}