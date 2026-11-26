# IR: {"sets":[],"params":["raw_material_cost_per_lb","lab_hours_per_lb_raw","regular_brute_oz_per_lb","regular_chanelle_oz_per_lb","regular_brute_price_per_oz","regular_chanelle_price_per_oz","luxury_brute_price_per_oz","luxury_chanelle_price_per_oz","brute_further_lab_hours_per_oz","chanelle_further_lab_hours_per_oz","brute_further_cost_per_oz","chanelle_further_cost_per_oz","lab_hours_capacity","raw_material_capacity_lb"],"variables":{"raw_lb":"continuous nonnegative","regular_brute_sold":"continuous nonnegative","regular_chanelle_sold":"continuous nonnegative","luxury_brute_sold":"continuous nonnegative","luxury_chanelle_sold":"continuous nonnegative"},"constraints":["regular_brute_sold + luxury_brute_sold = regular_brute_oz_per_lb * raw_lb","regular_chanelle_sold + luxury_chanelle_sold = regular_chanelle_oz_per_lb * raw_lb","lab_hours_per_lb_raw * raw_lb + brute_further_lab_hours_per_oz * luxury_brute_sold + chanelle_further_lab_hours_per_oz * luxury_chanelle_sold <= lab_hours_capacity","raw_lb <= raw_material_capacity_lb"],"objective":"maximize regular_brute_price_per_oz * regular_brute_sold + regular_chanelle_price_per_oz * regular_chanelle_sold + luxury_brute_price_per_oz * luxury_brute_sold + luxury_chanelle_price_per_oz * luxury_chanelle_sold - raw_material_cost_per_lb * raw_lb - brute_further_cost_per_oz * luxury_brute_sold - chanelle_further_cost_per_oz * luxury_chanelle_sold"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    parameter_names = (
        "raw_material_cost_per_lb",
        "lab_hours_per_lb_raw",
        "regular_brute_oz_per_lb",
        "regular_chanelle_oz_per_lb",
        "regular_brute_price_per_oz",
        "regular_chanelle_price_per_oz",
        "luxury_brute_price_per_oz",
        "luxury_chanelle_price_per_oz",
        "brute_further_lab_hours_per_oz",
        "chanelle_further_lab_hours_per_oz",
        "brute_further_cost_per_oz",
        "chanelle_further_cost_per_oz",
        "lab_hours_capacity",
        "raw_material_capacity_lb",
    )
    for parameter_name in parameter_names:
        model.add_component(
            parameter_name,
            pyo.Param(
                initialize=params[parameter_name],
                within=pyo.Reals,
            ),
        )

    model.raw_lb = pyo.Var(domain=pyo.NonNegativeReals)
    model.regular_brute_sold = pyo.Var(domain=pyo.NonNegativeReals)
    model.regular_chanelle_sold = pyo.Var(domain=pyo.NonNegativeReals)
    model.luxury_brute_sold = pyo.Var(domain=pyo.NonNegativeReals)
    model.luxury_chanelle_sold = pyo.Var(domain=pyo.NonNegativeReals)

    model.brute_balance = pyo.Constraint(
        expr=(
            model.regular_brute_sold + model.luxury_brute_sold
            == model.regular_brute_oz_per_lb * model.raw_lb
        )
    )
    model.chanelle_balance = pyo.Constraint(
        expr=(
            model.regular_chanelle_sold + model.luxury_chanelle_sold
            == model.regular_chanelle_oz_per_lb * model.raw_lb
        )
    )
    model.laboratory_capacity = pyo.Constraint(
        expr=(
            model.lab_hours_per_lb_raw * model.raw_lb
            + model.brute_further_lab_hours_per_oz * model.luxury_brute_sold
            + model.chanelle_further_lab_hours_per_oz
            * model.luxury_chanelle_sold
            <= model.lab_hours_capacity
        )
    )
    model.raw_purchase_capacity = pyo.Constraint(
        expr=model.raw_lb <= model.raw_material_capacity_lb
    )

    model.profit = pyo.Objective(
        expr=(
            model.regular_brute_price_per_oz * model.regular_brute_sold
            + model.regular_chanelle_price_per_oz * model.regular_chanelle_sold
            + model.luxury_brute_price_per_oz * model.luxury_brute_sold
            + model.luxury_chanelle_price_per_oz * model.luxury_chanelle_sold
            - model.raw_material_cost_per_lb * model.raw_lb
            - model.brute_further_cost_per_oz * model.luxury_brute_sold
            - model.chanelle_further_cost_per_oz * model.luxury_chanelle_sold
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected solver errors remain visible to the caller.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}