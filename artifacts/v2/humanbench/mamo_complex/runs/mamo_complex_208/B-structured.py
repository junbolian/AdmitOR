# IR: {"sets":{"F":[1,2,3,4,5]},"params":{"target_Ni":"scalar","target_Ph":"scalar","target_Po":"scalar","tol_Ni":"scalar","tol_Ph":"scalar","tol_Po":"scalar","nutrient_Ni":"F-indexed percentage","nutrient_Ph":"F-indexed percentage","nutrient_Po":"F-indexed percentage","price":"F-indexed cost per 100 pounds"},"variables":{"fraction[f]":"continuous, nonnegative; fraction of total blend"},"constraints":["sum(fraction[f] for f in F) = 1","target_Ni <= sum(nutrient_Ni[f]*fraction[f] for f in F) <= target_Ni + tol_Ni","target_Ph <= sum(nutrient_Ph[f]*fraction[f] for f in F) <= target_Ph + tol_Ph","target_Po <= sum(nutrient_Po[f]*fraction[f] for f in F) <= target_Po + tol_Po"],"objective":"minimize sum(price[f]*fraction[f] for f in F)/100; cost per pound"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_data(values):
    """Accept mappings keyed by 1..5 or '1'..'5', or five-item sequences."""
    if isinstance(values, Mapping):
        return {
            fertilizer: values[fertilizer]
            if fertilizer in values
            else values[str(fertilizer)]
            for fertilizer in range(1, 6)
        }
    return {
        fertilizer: values[fertilizer - 1]
        for fertilizer in range(1, 6)
    }


def solve(params):
    model = pyo.ConcreteModel()
    model.F = pyo.RangeSet(1, 5)

    model.target_Ni = pyo.Param(initialize=params["target_Ni"])
    model.target_Ph = pyo.Param(initialize=params["target_Ph"])
    model.target_Po = pyo.Param(initialize=params["target_Po"])

    model.tol_Ni = pyo.Param(initialize=params["tol_Ni"])
    model.tol_Ph = pyo.Param(initialize=params["tol_Ph"])
    model.tol_Po = pyo.Param(initialize=params["tol_Po"])

    model.nutrient_Ni = pyo.Param(
        model.F, initialize=_indexed_data(params["nutrient_Ni"])
    )
    model.nutrient_Ph = pyo.Param(
        model.F, initialize=_indexed_data(params["nutrient_Ph"])
    )
    model.nutrient_Po = pyo.Param(
        model.F, initialize=_indexed_data(params["nutrient_Po"])
    )
    model.price = pyo.Param(
        model.F, initialize=_indexed_data(params["price"])
    )

    model.fraction = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    model.blend_total = pyo.Constraint(
        expr=sum(model.fraction[fertilizer] for fertilizer in model.F) == 1
    )

    model.nitrogen_bounds = pyo.Constraint(
        expr=pyo.inequality(
            model.target_Ni,
            sum(
                model.nutrient_Ni[fertilizer] * model.fraction[fertilizer]
                for fertilizer in model.F
            ),
            model.target_Ni + model.tol_Ni,
        )
    )

    model.phosphorus_bounds = pyo.Constraint(
        expr=pyo.inequality(
            model.target_Ph,
            sum(
                model.nutrient_Ph[fertilizer] * model.fraction[fertilizer]
                for fertilizer in model.F
            ),
            model.target_Ph + model.tol_Ph,
        )
    )

    model.potash_bounds = pyo.Constraint(
        expr=pyo.inequality(
            model.target_Po,
            sum(
                model.nutrient_Po[fertilizer] * model.fraction[fertilizer]
                for fertilizer in model.F
            ),
            model.target_Po + model.tol_Po,
        )
    )

    # Convert the input prices per 100 pounds to cost per pound.
    model.cost_per_pound = pyo.Objective(
        expr=sum(
            model.price[fertilizer] * model.fraction[fertilizer]
            for fertilizer in model.F
        ) / 100,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected runtime errors remain visible to the caller.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.cost_per_pound))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}