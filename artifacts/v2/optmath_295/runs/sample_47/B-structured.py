# IR: {"sets":{"A":[0,1,2,3],"P":[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]]},"params":["expected_returns[A]","min_return","sum_allocation","max_weight","variances[A]","covariances[P]"],"variables":{"weight[A]":{"type":"continuous","lower_bound":0,"upper_bound":"max_weight"}},"constraints":["sum(weight[i] for i in A) == sum_allocation","sum(expected_returns[i]*weight[i] for i in A) >= min_return"],"objective":{"sense":"minimize","expression":"sum(variances[i]*weight[i]**2 for i in A) + 2*sum(covariances[i,j]*weight[i]*weight[j] for (i,j) in P)"}}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    asset_indices = (0, 1, 2, 3)
    covariance_pairs = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))

    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    sum_allocation = params["sum_allocation"]
    max_weight = params["max_weight"]
    variances = params["variances"]
    covariances = params["covariances"]

    if isinstance(covariances, Mapping):
        covariance_values = {
            pair: covariances[pair] for pair in covariance_pairs
        }
    else:
        covariance_values = dict(zip(covariance_pairs, covariances))
        if len(covariance_values) != len(covariance_pairs):
            raise ValueError("covariances must contain all six covariance terms.")

    model = pyo.ConcreteModel()

    model.assets = pyo.Set(initialize=asset_indices, ordered=True)
    model.asset_pairs = pyo.Set(
        initialize=covariance_pairs, dimen=2, ordered=True
    )

    model.expected_returns = pyo.Param(
        model.assets,
        initialize={idx: expected_returns[idx] for idx in asset_indices},
        within=pyo.Reals,
    )
    model.min_return = pyo.Param(initialize=min_return, within=pyo.Reals)
    model.sum_allocation = pyo.Param(
        initialize=sum_allocation, within=pyo.Reals
    )
    model.max_weight = pyo.Param(
        initialize=max_weight, within=pyo.NonNegativeReals
    )
    model.variances = pyo.Param(
        model.assets,
        initialize={idx: variances[idx] for idx in asset_indices},
        within=pyo.Reals,
    )
    model.covariances = pyo.Param(
        model.asset_pairs,
        initialize=covariance_values,
        within=pyo.Reals,
    )

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
        bounds=(0, model.max_weight),
    )

    model.total_allocation_constraint = pyo.Constraint(
        expr=sum(model.weight[idx] for idx in model.assets)
        == model.sum_allocation
    )
    model.minimum_return_constraint = pyo.Constraint(
        expr=sum(
            model.expected_returns[idx] * model.weight[idx]
            for idx in model.assets
        )
        >= model.min_return
    )

    model.portfolio_variance = pyo.Objective(
        expr=sum(
            model.variances[idx] * model.weight[idx] ** 2
            for idx in model.assets
        )
        + 2
        * sum(
            model.covariances[left, right]
            * model.weight[left]
            * model.weight[right]
            for left, right in model.asset_pairs
        ),
        sense=pyo.minimize,
    )

    # Some APPsi HiGHS versions reject quadratic objectives. Handle that
    # solver failure without importing DegreeError from a version-specific
    # location or changing the mathematical model.
    try:
        Highs().solve(model)
    except Exception as exc:
        if type(exc).__name__ == "DegreeError":
            return {
                "objective": None,
                "status": "unsupported_quadratic_objective",
            }
        if isinstance(exc, RuntimeError) and (
            "a feasible solution was not found" in str(exc).lower()
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.portfolio_variance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}