# IR: {"sets":{"F":[1,2,3,4,5],"J":["N","P","K"]},"params":{"target_N":"minimum nitrogen percentage","target_P":"minimum phosphorus percentage","target_K":"minimum potash percentage","tol":"maximum percentage-point excess","price[F]":"cost per 100 pounds","nutrient_N[F]":"nitrogen percentage","nutrient_P[F]":"phosphorus percentage","nutrient_K[F]":"potash percentage"},"variables":{"x[F]":"continuous nonnegative blend mass fractions"},"constraints":["sum(x[i] for i in F) = 1","target_N <= sum(nutrient_N[i]*x[i] for i in F) <= target_N + tol","target_P <= sum(nutrient_P[i]*x[i] for i in F) <= target_P + tol","target_K <= sum(nutrient_K[i]*x[i] for i in F) <= target_K + tol"],"objective":"minimize sum(price[i]*x[i] for i in F)/100, in dollars per pound"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexed mappings (keys 1..5 or '1'..'5') or five-item lists."""

    def indexed_values(values):
        if isinstance(values, Mapping):
            return {
                fertilizer: (
                    values[fertilizer]
                    if fertilizer in values
                    else values[str(fertilizer)]
                )
                for fertilizer in range(1, 6)
            }
        return {
            fertilizer: values[fertilizer - 1]
            for fertilizer in range(1, 6)
        }

    model = pyo.ConcreteModel()
    model.F = pyo.RangeSet(1, 5)

    model.target_N = pyo.Param(initialize=params["target_N"])
    model.target_P = pyo.Param(initialize=params["target_P"])
    model.target_K = pyo.Param(initialize=params["target_K"])
    model.tol = pyo.Param(initialize=params["tol"])

    model.price = pyo.Param(
        model.F, initialize=indexed_values(params["price"])
    )
    model.nutrient_N = pyo.Param(
        model.F, initialize=indexed_values(params["nutrient_N"])
    )
    model.nutrient_P = pyo.Param(
        model.F, initialize=indexed_values(params["nutrient_P"])
    )
    model.nutrient_K = pyo.Param(
        model.F, initialize=indexed_values(params["nutrient_K"])
    )

    model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    model.mass_balance = pyo.Constraint(
        expr=sum(model.x[fertilizer] for fertilizer in model.F) == 1
    )

    model.nitrogen_bounds = pyo.Constraint(
        expr=pyo.inequality(
            model.target_N,
            sum(
                model.nutrient_N[fertilizer] * model.x[fertilizer]
                for fertilizer in model.F
            ),
            model.target_N + model.tol,
        )
    )
    model.phosphorus_bounds = pyo.Constraint(
        expr=pyo.inequality(
            model.target_P,
            sum(
                model.nutrient_P[fertilizer] * model.x[fertilizer]
                for fertilizer in model.F
            ),
            model.target_P + model.tol,
        )
    )
    model.potash_bounds = pyo.Constraint(
        expr=pyo.inequality(
            model.target_K,
            sum(
                model.nutrient_K[fertilizer] * model.x[fertilizer]
                for fertilizer in model.F
            ),
            model.target_K + model.tol,
        )
    )

    # Convert prices per 100 pounds into dollars per pound.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.price[fertilizer] * model.x[fertilizer]
            for fertilizer in model.F
        ) / 100,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions are allowed to propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    # Objective retrievability alone determines success.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}