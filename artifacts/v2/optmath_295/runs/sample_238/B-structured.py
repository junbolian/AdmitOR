# IR: {"sets":{"foods":"0..23","nutrients":"0..10"},"params":{"cost":"cost[j] from params['cost'][j]","nutrient_min":"minimum[i] from params['nutrient_min'][i]","nutrient_max":"maximum[i] from params['nutrient_max'][i]","nutrient_coeff":"coefficient[i,j] from params['nutrient_coeff'][i][j]"},"variables":{"quantity[j]":"NonNegativeReals for j in foods"},"constraints":["nutrient_lower[i]: sum(coefficient[i,j]*quantity[j] for j in foods) >= minimum[i] for i in nutrients","nutrient_upper[i]: sum(coefficient[i,j]*quantity[j] for j in foods) <= maximum[i] for i in nutrients"],"objective":"minimize sum(cost[j]*quantity[j] for j in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the continuous diet LP using zero-indexed input arrays."""
    cost = params["cost"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    nutrient_coeff = params["nutrient_coeff"]

    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 23)
    model.nutrients = pyo.RangeSet(0, 10)

    model.cost = pyo.Param(
        model.foods,
        initialize=lambda mdl, food: cost[food],
        within=pyo.Reals,
    )
    model.minimum = pyo.Param(
        model.nutrients,
        initialize=lambda mdl, nutrient: nutrient_min[nutrient],
        within=pyo.Reals,
    )
    model.maximum = pyo.Param(
        model.nutrients,
        initialize=lambda mdl, nutrient: nutrient_max[nutrient],
        within=pyo.Reals,
    )
    model.coefficient = pyo.Param(
        model.nutrients,
        model.foods,
        initialize=lambda mdl, nutrient, food: nutrient_coeff[nutrient][food],
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    def nutrient_lower_rule(mdl, nutrient):
        return sum(
            mdl.coefficient[nutrient, food] * mdl.quantity[food]
            for food in mdl.foods
        ) >= mdl.minimum[nutrient]

    def nutrient_upper_rule(mdl, nutrient):
        return sum(
            mdl.coefficient[nutrient, food] * mdl.quantity[food]
            for food in mdl.foods
        ) <= mdl.maximum[nutrient]

    model.nutrient_lower = pyo.Constraint(
        model.nutrients, rule=nutrient_lower_rule
    )
    model.nutrient_upper = pyo.Constraint(
        model.nutrients, rule=nutrient_upper_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.quantity[food] for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}