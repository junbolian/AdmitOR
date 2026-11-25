# IR: {"sets":{"F":"range(params['num_foods'])","N":"range(params['num_nutrients'])"},"params":{"food_cost":"cost[i], i in F","nutrient_min":"lower[j], j in N","nutrient_max":"upper[j], j in N","nutrient_0_coeff..nutrient_10_coeff":"a[j,i], j in N, i in F","num_foods":"frozen food set size","num_nutrients":"frozen nutrient set size"},"variables":{"quantity[i]":"nonnegative continuous, i in F"},"constraints":["sum(a[j,i]*quantity[i] for i in F) >= lower[j], j in N","sum(a[j,i]*quantity[i] for i in F) <= upper[j], j in N"],"objective":"minimize sum(cost[i]*quantity[i] for i in F)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(values, position, prefix):
    """Accept sequences or mappings keyed by integer, string, or item label."""
    if isinstance(values, Mapping):
        if position in values:
            return values[position]
        if str(position) in values:
            return values[str(position)]
        return values[f"{prefix}_{position}"]
    return values[position]


def solve(params):
    num_foods = int(params["num_foods"])
    num_nutrients = int(params["num_nutrients"])

    food_cost = params["food_cost"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    nutrient_coefficients = [
        params[f"nutrient_{j}_coeff"] for j in range(num_nutrients)
    ]

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=range(num_foods), ordered=True)
    model.N = pyo.Set(initialize=range(num_nutrients), ordered=True)

    model.cost = pyo.Param(
        model.F,
        initialize={i: _entry(food_cost, i, "food") for i in model.F},
        within=pyo.Reals,
    )
    model.lower_intake = pyo.Param(
        model.N,
        initialize={j: _entry(nutrient_min, j, "nutrient") for j in model.N},
        within=pyo.Reals,
    )
    model.upper_intake = pyo.Param(
        model.N,
        initialize={j: _entry(nutrient_max, j, "nutrient") for j in model.N},
        within=pyo.Reals,
    )
    model.coefficient = pyo.Param(
        model.N,
        model.F,
        initialize={
            (j, i): _entry(nutrient_coefficients[j], i, "food")
            for j in model.N
            for i in model.F
        },
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    def minimum_rule(mod, j):
        return (
            sum(mod.coefficient[j, i] * mod.quantity[i] for i in mod.F)
            >= mod.lower_intake[j]
        )

    def maximum_rule(mod, j):
        return (
            sum(mod.coefficient[j, i] * mod.quantity[i] for i in mod.F)
            <= mod.upper_intake[j]
        )

    model.minimum_intake = pyo.Constraint(model.N, rule=minimum_rule)
    model.maximum_intake = pyo.Constraint(model.N, rule=maximum_rule)
    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i] * model.quantity[i] for i in model.F),
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