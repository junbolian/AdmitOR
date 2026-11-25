# IR: {"sets":{"A":[0,1,2,3],"P":[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]],"C":"Feasible stationary points obtained from nonsingular KKT systems for the budget equality and every subset of at most three active bound/return inequalities"},"params":["expected_returns","variances","covariances","min_return","budget_fraction","max_asset_weight"],"variables":{"weight[a]":"continuous, 0 <= weight[a] <= max_asset_weight","choose[c]":"binary"},"constraints":["sum(weight[a]) = budget_fraction","sum(expected_returns[a]*weight[a]) >= min_return","sum(choose[c]) = 1","weight[a] = sum(C[c][a]*choose[c]) for each a"],"objective":"minimize sum(choose[c] * (sum(variances[a]*C[c][a]^2) + 2*sum(covariances[a,b]*C[c][a]*C[c][b])))"}
#
# Dependencies: numpy, pyomo, highspy.
#
# Pyomo's APPSI HiGHS interface does not accept quadratic objectives.
# This script therefore uses an equivalent finite-candidate MILP.
# Enumerating stationary points on all faces also handles indefinite
# covariance matrices. On a bounded polytope, a quadratic has a minimizer
# with a nonsingular face KKT system: any flat minimizing direction can
# be followed to a smaller face without changing the objective.

from itertools import combinations

import numpy as np
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    asset_count = 4
    pairs = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))

    expected_returns = np.asarray(params["expected_returns"], dtype=float)
    variances = np.asarray(params["variances"], dtype=float)
    covariances = np.asarray(params["covariances"], dtype=float)
    min_return = float(params["min_return"])
    budget_fraction = float(params["budget_fraction"])
    max_asset_weight = float(params["max_asset_weight"])

    if expected_returns.shape != (asset_count,):
        raise ValueError("expected_returns must contain four values.")
    if variances.shape != (asset_count,):
        raise ValueError("variances must contain four values.")
    if covariances.shape != (len(pairs),):
        raise ValueError("covariances must contain six values.")

    numeric_data = np.concatenate(
        (
            expected_returns,
            variances,
            covariances,
            [min_return, budget_fraction, max_asset_weight],
        )
    )
    if not np.isfinite(numeric_data).all():
        raise ValueError("All parameter values must be finite.")

    if (
        max_asset_weight < 0
        or budget_fraction < 0
        or budget_fraction > asset_count * max_asset_weight
    ):
        return {"objective": None, "status": "infeasible"}

    covariance_matrix = np.diag(variances)
    for pair_index, (left_asset, right_asset) in enumerate(pairs):
        covariance_matrix[left_asset, right_asset] = covariances[pair_index]
        covariance_matrix[right_asset, left_asset] = covariances[pair_index]

    # Inequalities have the common form G @ weight <= h.
    identity = np.eye(asset_count)
    inequality_matrix = np.vstack(
        (-identity, identity, -expected_returns.reshape(1, asset_count))
    )
    inequality_rhs = np.concatenate(
        (
            np.zeros(asset_count),
            np.full(asset_count, max_asset_weight),
            [-min_return],
        )
    )

    # Row scaling improves numerical conditioning without changing the model.
    row_scales = np.maximum(
        np.max(np.abs(inequality_matrix), axis=1),
        np.abs(inequality_rhs),
    )
    row_scales[row_scales == 0] = 1.0
    scaled_matrix = inequality_matrix / row_scales[:, None]
    scaled_rhs = inequality_rhs / row_scales

    quadratic_scale = float(np.max(np.abs(covariance_matrix)))
    if quadratic_scale == 0:
        quadratic_scale = 1.0
    scaled_hessian = 2.0 * covariance_matrix / quadratic_scale

    candidates = []
    candidate_risks = []
    feasibility_tolerance = 1e-9
    inequality_indices = range(inequality_matrix.shape[0])

    for active_count in range(asset_count):
        for active_indices in combinations(inequality_indices, active_count):
            active_rows = list(active_indices)
            equality_matrix = np.vstack(
                (
                    np.ones((1, asset_count)),
                    scaled_matrix[active_rows, :],
                )
            )
            equality_rhs = np.concatenate(
                ([budget_fraction], scaled_rhs[active_rows])
            )

            equality_count = equality_matrix.shape[0]
            kkt_matrix = np.block(
                [
                    [scaled_hessian, equality_matrix.T],
                    [
                        equality_matrix,
                        np.zeros((equality_count, equality_count)),
                    ],
                ]
            )
            kkt_rhs = np.concatenate(
                (np.zeros(asset_count), equality_rhs)
            )

            try:
                solution = np.linalg.solve(kkt_matrix, kkt_rhs)
            except np.linalg.LinAlgError:
                # Dependent active constraints or flat stationary directions
                # are represented by other, lower-dimensional faces.
                continue

            candidate = solution[:asset_count]
            if not np.isfinite(candidate).all():
                continue

            budget_error = abs(float(candidate.sum()) - budget_fraction)
            budget_tolerance = feasibility_tolerance * (
                1.0 + abs(budget_fraction)
            )
            if budget_error > budget_tolerance:
                continue

            residuals = scaled_matrix @ candidate - scaled_rhs
            if np.any(residuals > feasibility_tolerance):
                continue

            candidates.append(tuple(float(value) for value in candidate))
            candidate_risks.append(
                float(candidate @ covariance_matrix @ candidate)
            )

    if not candidates:
        return {"objective": None, "status": "no_feasible_candidate"}

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, asset_count - 1)
    model.candidates = pyo.RangeSet(0, len(candidates) - 1)

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
        bounds=(0.0, max_asset_weight),
    )
    model.choose = pyo.Var(model.candidates, domain=pyo.Binary)

    model.budget_constraint = pyo.Constraint(
        expr=sum(model.weight[asset] for asset in model.assets)
        == budget_fraction
    )
    model.return_constraint = pyo.Constraint(
        expr=sum(
            float(expected_returns[asset]) * model.weight[asset]
            for asset in model.assets
        )
        >= min_return
    )
    model.single_candidate_constraint = pyo.Constraint(
        expr=sum(
            model.choose[candidate_index]
            for candidate_index in model.candidates
        )
        == 1
    )

    def candidate_weight_rule(instance, asset):
        return instance.weight[asset] == sum(
            candidates[candidate_index][asset]
            * instance.choose[candidate_index]
            for candidate_index in instance.candidates
        )

    model.candidate_weight_constraint = pyo.Constraint(
        model.assets, rule=candidate_weight_rule
    )

    model.portfolio_variance = pyo.Objective(
        expr=sum(
            candidate_risks[candidate_index]
            * model.choose[candidate_index]
            for candidate_index in model.candidates
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        # Other runtime errors are unexpected and should propagate.
        message = str(exc).lower()
        if "feasible solution was not found" in message:
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.portfolio_variance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}