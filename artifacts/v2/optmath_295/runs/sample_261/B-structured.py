# IR: {"sets":{"foods":"0..14","nutrients":"0..8"},"params":{"cost_per_serving":"[food]","nutrient_min":"[nutrient]","nutrient_max":"[nutrient]","volume_per_serving":"[food]","total_volume_capacity":"scalar","nutrient_per_serving":"[food][nutrient], required but omitted from the stated inputs"},"variables":{"servings[food]":"NonNegativeReals"},"constraints":["For each nutrient j: sum(nutrient_per_serving[i][j]*servings[i] for i in foods) >= nutrient_min[j].","For each nutrient j: sum(nutrient_per_serving[i][j]*servings[i] for i in foods) <= nutrient_max[j].","sum(volume_per_serving[i]*servings[i] for i in foods) <= total_volume_capacity."],"objective":"minimize sum(cost_per_serving[i]*servings[i] for i in foods)","failure_policy":"Return missing_nutrient_data if the nutrient matrix is absent; return solver_failed or objective_unavailable for the corresponding failures."}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(values, position, prefix):
    """Read a sequence, integer-keyed mapping, or named-key mapping."""
    if isinstance(values, Mapping):
        if position in values:
            return values[position]
        return values[f"{prefix}_{position}"]
    return values[position]


def solve(params):
    """
    Build and solve the continuous diet linear program.

    The five listed parameters do not specify the nutritional constraints:
    the full 15-by-9 nutrient contribution matrix is missing. The examples
    specify only six of its 135 entries.

    Consequently, no mathematically valid script can compute the requested
    optimum from those five parameters alone. The previous failure reflects
    missing problem data, rather than a solver or modeling error.

    To make the problem solvable, also provide
    params["nutrient_per_serving"], indexed first by food and then nutrient.
    This implementation never fabricates unspecified nutrient coefficients.
    """
    cost_per_serving = params["cost_per_serving"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    volume_per_serving = params["volume_per_serving"]
    total_volume_capacity = params["total_volume_capacity"]

    if (
        "nutrient_per_serving" not in params
        or params["nutrient_per_serving"] is None
    ):
        return {"objective": None, "status": "missing_nutrient_data"}

    nutrient_per_serving = params["nutrient_per_serving"]

    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 14)
    model.nutrients = pyo.RangeSet(0, 8)

    model.food_cost = pyo.Param(
        model.foods,
        initialize=lambda mdl, i: _indexed_value(
            cost_per_serving, i, "food"
        ),
        within=pyo.Reals,
    )
    model.nutrient_lower = pyo.Param(
        model.nutrients,
        initialize=lambda mdl, j: _indexed_value(
            nutrient_min, j, "nutrient"
        ),
        within=pyo.Reals,
    )
    model.nutrient_upper = pyo.Param(
        model.nutrients,
        initialize=lambda mdl, j: _indexed_value(
            nutrient_max, j, "nutrient"
        ),
        within=pyo.Reals,
    )
    model.food_volume = pyo.Param(
        model.foods,
        initialize=lambda mdl, i: _indexed_value(
            volume_per_serving, i, "food"
        ),
        within=pyo.NonNegativeReals,
    )
    model.volume_capacity = pyo.Param(
        initialize=total_volume_capacity,
        within=pyo.NonNegativeReals,
    )
    model.nutrient_content = pyo.Param(
        model.foods,
        model.nutrients,
        initialize=lambda mdl, i, j: _indexed_value(
            _indexed_value(nutrient_per_serving, i, "food"),
            j,
            "nutrient",
        ),
        within=pyo.NonNegativeReals,
    )

    model.servings = pyo.Var(
        model.foods,
        domain=pyo.NonNegativeReals,
    )

    def nutrient_lower_rule(mdl, j):
        return (
            pyo.quicksum(
                mdl.nutrient_content[i, j] * mdl.servings[i]
                for i in mdl.foods
            )
            >= mdl.nutrient_lower[j]
        )

    def nutrient_upper_rule(mdl, j):
        return (
            pyo.quicksum(
                mdl.nutrient_content[i, j] * mdl.servings[i]
                for i in mdl.foods
            )
            <= mdl.nutrient_upper[j]
        )

    model.nutrient_minimum_constraints = pyo.Constraint(
        model.nutrients,
        rule=nutrient_lower_rule,
    )
    model.nutrient_maximum_constraints = pyo.Constraint(
        model.nutrients,
        rule=nutrient_upper_rule,
    )
    model.volume_constraint = pyo.Constraint(
        expr=pyo.quicksum(
            model.food_volume[i] * model.servings[i]
            for i in model.foods
        )
        <= model.volume_capacity
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.food_cost[i] * model.servings[i]
            for i in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}