# IR: {"sets":{"A":[0,1,2,3,4]},"params":{"expected_returns":"params vector indexed by A","min_return":"params scalar","max_weight":"params scalar","budget_sum_weights":"params scalar","covariances":"required supplemental params matrix indexed by A x A; absent from the problem statement"},"variables":{"weight[a]":"continuous nonnegative; upper bound max_weight"},"constraints":["sum(weight[a] for a in A) == budget_sum_weights","sum(expected_returns[a]*weight[a] for a in A) >= min_return"],"objective":"minimize sum(covariances[a][b]*weight[a]*weight[b] for a,b in A)","failure_policy":["missing covariance matrix => missing_covariances","unsupported quadratic expression => unsupported_quadratic","solver cannot load a feasible solution => no_feasible_solution","objective evaluation fails => objective_unavailable"]}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs, DegreeError


def solve(params):
    """Minimize portfolio variance when the required covariance data exist.

    The previous missing_covariances result identifies missing problem data,
    not an implementation defect. Expected returns do not determine asset
    variances or covariances. Consequently, no script can compute the requested
    minimum variance from the four listed parameters alone without inventing
    data or changing the objective.

    This implementation accepts an additional params["covariances"] matrix.
    The required APPsi HiGHS interface may reject its quadratic objective;
    that limitation is reported instead of substituting a different model.
    """
    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    max_weight = params["max_weight"]
    budget_sum_weights = params["budget_sum_weights"]

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, 4)

    model.asset_returns = pyo.Param(
        model.assets,
        initialize=lambda mdl, asset: expected_returns[asset],
        within=pyo.Reals,
    )
    model.required_return = pyo.Param(
        initialize=min_return,
        within=pyo.Reals,
    )
    model.weight_limit = pyo.Param(
        initialize=max_weight,
        within=pyo.NonNegativeReals,
    )
    model.total_allocation = pyo.Param(
        initialize=budget_sum_weights,
        within=pyo.NonNegativeReals,
    )

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
        bounds=lambda mdl, asset: (0, mdl.weight_limit),
    )

    model.allocation_constraint = pyo.Constraint(
        expr=sum(model.weight[asset] for asset in model.assets)
        == model.total_allocation
    )
    model.minimum_return_constraint = pyo.Constraint(
        expr=sum(
            model.asset_returns[asset] * model.weight[asset]
            for asset in model.assets
        )
        >= model.required_return
    )

    # A zero, identity, or returns-derived matrix would invent risk data.
    if "covariances" not in params:
        return {"objective": None, "status": "missing_covariances"}

    covariances = params["covariances"]
    model.asset_covariance = pyo.Param(
        model.assets,
        model.assets,
        initialize=lambda mdl, asset, other_asset: (
            covariances[asset][other_asset]
        ),
        within=pyo.Reals,
    )
    model.variance_objective = pyo.Objective(
        expr=sum(
            model.asset_covariance[asset, other_asset]
            * model.weight[asset]
            * model.weight[other_asset]
            for asset in model.assets
            for other_asset in model.assets
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except DegreeError:
        return {"objective": None, "status": "unsupported_quadratic"}
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.variance_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}