# IR: {"sets":[],"params":{"raw_cost":"raw_material_cost_per_lb","processing_hours":"lab_hours_per_lb_processing","brute_yield":"brute_oz_per_lb","chanelle_yield":"chanelle_oz_per_lb","regular_brute_price":"regular_brute_price_per_oz","regular_chanelle_price":"regular_chanelle_price_per_oz","luxury_brute_price":"luxury_brute_price_per_oz","luxury_chanelle_price":"luxury_chanelle_price_per_oz","luxury_brute_hours":"luxury_brute_lab_hours_per_oz","luxury_chanelle_hours":"luxury_chanelle_lab_hours_per_oz","luxury_brute_cost":"luxury_brute_cost_per_oz","luxury_chanelle_cost":"luxury_chanelle_cost_per_oz","lab_capacity":"lab_hours_capacity","raw_capacity":"raw_material_capacity_lb"},"variables":{"raw_lb":"nonnegative continuous","regular_brute_oz":"nonnegative continuous","regular_chanelle_oz":"nonnegative continuous","luxury_brute_oz":"nonnegative continuous","luxury_chanelle_oz":"nonnegative continuous"},"constraints":["regular_brute_oz + luxury_brute_oz = brute_yield * raw_lb","regular_chanelle_oz + luxury_chanelle_oz = chanelle_yield * raw_lb","processing_hours * raw_lb + luxury_brute_hours * luxury_brute_oz + luxury_chanelle_hours * luxury_chanelle_oz <= lab_capacity","raw_lb <= raw_capacity"],"objective":"maximize regular_brute_price * regular_brute_oz + regular_chanelle_price * regular_chanelle_oz + luxury_brute_price * luxury_brute_oz + luxury_chanelle_price * luxury_chanelle_oz - raw_cost * raw_lb - luxury_brute_cost * luxury_brute_oz - luxury_chanelle_cost * luxury_chanelle_oz"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.raw_cost = pyo.Param(
        initialize=params["raw_material_cost_per_lb"]
    )
    model.processing_hours = pyo.Param(
        initialize=params["lab_hours_per_lb_processing"]
    )
    model.brute_yield = pyo.Param(
        initialize=params["brute_oz_per_lb"]
    )
    model.chanelle_yield = pyo.Param(
        initialize=params["chanelle_oz_per_lb"]
    )
    model.regular_brute_price = pyo.Param(
        initialize=params["regular_brute_price_per_oz"]
    )
    model.regular_chanelle_price = pyo.Param(
        initialize=params["regular_chanelle_price_per_oz"]
    )
    model.luxury_brute_price = pyo.Param(
        initialize=params["luxury_brute_price_per_oz"]
    )
    model.luxury_chanelle_price = pyo.Param(
        initialize=params["luxury_chanelle_price_per_oz"]
    )
    model.luxury_brute_hours = pyo.Param(
        initialize=params["luxury_brute_lab_hours_per_oz"]
    )
    model.luxury_chanelle_hours = pyo.Param(
        initialize=params["luxury_chanelle_lab_hours_per_oz"]
    )
    model.luxury_brute_cost = pyo.Param(
        initialize=params["luxury_brute_cost_per_oz"]
    )
    model.luxury_chanelle_cost = pyo.Param(
        initialize=params["luxury_chanelle_cost_per_oz"]
    )
    model.lab_capacity = pyo.Param(
        initialize=params["lab_hours_capacity"]
    )
    model.raw_capacity = pyo.Param(
        initialize=params["raw_material_capacity_lb"]
    )

    # Raw material is purchased and processed; perfume variables are sales.
    # Luxury output consumes an equal quantity of regular perfume.
    model.raw_lb = pyo.Var(domain=pyo.NonNegativeReals)
    model.regular_brute_oz = pyo.Var(domain=pyo.NonNegativeReals)
    model.regular_chanelle_oz = pyo.Var(domain=pyo.NonNegativeReals)
    model.luxury_brute_oz = pyo.Var(domain=pyo.NonNegativeReals)
    model.luxury_chanelle_oz = pyo.Var(domain=pyo.NonNegativeReals)

    model.brute_balance = pyo.Constraint(
        expr=(
            model.regular_brute_oz + model.luxury_brute_oz
            == model.brute_yield * model.raw_lb
        )
    )
    model.chanelle_balance = pyo.Constraint(
        expr=(
            model.regular_chanelle_oz + model.luxury_chanelle_oz
            == model.chanelle_yield * model.raw_lb
        )
    )
    model.lab_limit = pyo.Constraint(
        expr=(
            model.processing_hours * model.raw_lb
            + model.luxury_brute_hours * model.luxury_brute_oz
            + model.luxury_chanelle_hours * model.luxury_chanelle_oz
            <= model.lab_capacity
        )
    )
    model.raw_limit = pyo.Constraint(
        expr=model.raw_lb <= model.raw_capacity
    )

    # Fixed laboratory costs do not affect the production decision.
    model.profit = pyo.Objective(
        expr=(
            model.regular_brute_price * model.regular_brute_oz
            + model.regular_chanelle_price * model.regular_chanelle_oz
            + model.luxury_brute_price * model.luxury_brute_oz
            + model.luxury_chanelle_price * model.luxury_chanelle_oz
            - model.raw_cost * model.raw_lb
            - model.luxury_brute_cost * model.luxury_brute_oz
            - model.luxury_chanelle_cost * model.luxury_chanelle_oz
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}