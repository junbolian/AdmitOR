# IR: {"sets":{"F":"range(params['num_foods'])","N":"range(params['num_nutrients'])"},"params":{"food_cost":"real[F]","nutrient_min":"real[N]","nutrient_max":"real[N]","nutrient_0_coeff":"real[F]","nutrient_1_coeff":"real[F]","nutrient_2_coeff":"real[F]","nutrient_3_coeff":"real[F]","nutrient_4_coeff":"real[F]","nutrient_5_coeff":"real[F]","nutrient_6_coeff":"real[F]","nutrient_7_coeff":"real[F]","nutrient_8_coeff":"real[F]","nutrient_9_coeff":"real[F]","nutrient_10_coeff":"real[F]","num_foods":"integer, frozen","num_nutrients":"integer, frozen"},"variables":{"quantity[f]":"nonnegative continuous, f in F"},"constraints":["sum(coeff[n,f]*quantity[f] for f in F) >= nutrient_min[n], n in N","sum(coeff[n,f]*quantity[f] for f in F) <= nutrient_max[n], n in N"],"objective":"minimize sum(food_cost[f]*quantity[f] for f in F)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, idx, prefix):
    """Accept sequences or mappings keyed by integer, string integer, or label."""
    if isinstance(data, Mapping):
        if idx in data:
            return data[idx]
        if str(idx) in data:
            return data[str(idx)]
        return data[f"{prefix}_{idx}"]
    return data[idx]


def solve(params):
    num_foods = int(params["num_foods"])
    num_nutrients = int(params["num_nutrients"])

    food_cost = params["food_cost"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    nutrient_coeff = [
        params["nutrient_0_coeff"],
        params["nutrient_1_coeff"],
        params["nutrient_2_coeff"],
        params["nutrient_3_coeff"],
        params["nutrient_4_coeff"],
        params["nutrient_5_coeff"],
        params["nutrient_6_coeff"],
        params["nutrient_7_coeff"],
        params["nutrient_8_coeff"],
        params["nutrient_9_coeff"],
        params["nutrient_10_coeff"],
    ]

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=range(num_foods), ordered=True)
    model.N = pyo.Set(initialize=range(num_nutrients), ordered=True)

    model.food_cost = pyo.Param(
        model.F,
        initialize=lambda mdl, food: _entry(food_cost, food, "food"),
        within=pyo.Reals,
    )
    model.nutrient_min = pyo.Param(
        model.N,
        initialize=lambda mdl, nutrient: _entry(
            nutrient_min, nutrient, "nutrient"
        ),
        within=pyo.Reals,
    )
    model.nutrient_max = pyo.Param(
        model.N,
        initialize=lambda mdl, nutrient: _entry(
            nutrient_max, nutrient, "nutrient"
        ),
        within=pyo.Reals,
    )
    model.coeff = pyo.Param(
        model.N,
        model.F,
        initialize=lambda mdl, nutrient, food: _entry(
            nutrient_coeff[nutrient], food, "food"
        ),
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    def minimum_rule(mdl, nutrient):
        return (
            sum(mdl.coeff[nutrient, food] * mdl.quantity[food] for food in mdl.F)
            >= mdl.nutrient_min[nutrient]
        )

    def maximum_rule(mdl, nutrient):
        return (
            sum(mdl.coeff[nutrient, food] * mdl.quantity[food] for food in mdl.F)
            <= mdl.nutrient_max[nutrient]
        )

    model.minimum_intake = pyo.Constraint(model.N, rule=minimum_rule)
    model.maximum_intake = pyo.Constraint(model.N, rule=maximum_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.food_cost[food] * model.quantity[food] for food in model.F
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}