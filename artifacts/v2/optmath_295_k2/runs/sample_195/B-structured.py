# {"sets":{"assets":[0,1,2,3],"pairs":[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]],"candidates":"feasible stationary points obtained by enumerating up to three active inequalities alongside the budget equality"},"params":["expected_returns","min_expected_return","variances","covariances","max_weight","budget_sum"],"candidate_generation":"For each active set, solve the equality-constrained variance KKT system; discard singular systems and infeasible points. A bounded feasible quadratic program has an optimum among these candidates.","variables":{"weight[assets]":"continuous, 0 <= weight <= max_weight","selected[candidates]":"binary"},"constraints":["sum(selected[c]) = 1","weight[i] = sum(candidate[c,i]*selected[c]) for each asset i","sum(weight[i]) = budget_sum","sum(expected_returns[i]*weight[i]) >= min_expected_return"],"objective":"minimize sum(variance(candidate[c])*selected[c]); binary selection makes this exactly the variance of the selected portfolio"}
from itertools import combinations

import numpy as np
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = np.asarray(params["expected_returns"], dtype=float)
    min_expected_return = float(params["min_expected_return"])
    variances = np.asarray(params["variances"], dtype=float)
    covariances = np.asarray(params["covariances"], dtype=float)
    max_weight = float(params["max_weight"])
    budget_sum = float(params["budget_sum"])

    if expected_returns.shape != (4,):
        raise ValueError("expected_returns must contain four values.")
    if variances.shape != (4,):
        raise ValueError("variances must contain four values.")
    if covariances.shape != (6,):
        raise ValueError("covariances must contain six values.")

    scalar_params = np.array(
        [min_expected_return, max_weight, budget_sum], dtype=float
    )
    if not all(
        np.all(np.isfinite(values))
        for values in (
            expected_returns,
            variances,
            covariances,
            scalar_params,
        )
    ):
        raise ValueError("All parameter values must be finite.")

    assets = range(4)
    pairs = tuple(combinations(assets, 2))

    covariance_matrix = np.diag(variances)
    for pair_index, (asset_i, asset_j) in enumerate(pairs):
        covariance_matrix[asset_i, asset_j] = covariances[pair_index]
        covariance_matrix[asset_j, asset_i] = covariances[pair_index]

    # APPsi HiGHS does not accept quadratic objectives. The supplied covariance
    # matrix also need not be positive semidefinite. Enumerating stationary
    # points of every face gives an exact finite reformulation, subject to
    # ordinary floating-point feasibility tolerances.
    #
    # To see completeness, choose a global minimizer on a face of smallest
    # dimension. Its restricted Hessian must be positive definite: a null
    # direction would preserve the objective until reaching a smaller face.
    # Its independent active constraints therefore yield a nonsingular KKT
    # system included below. Vertices are included as zero-dimensional faces.

    identity = np.eye(4)
    inequality_matrix = np.vstack(
        (-identity, identity, -expected_returns.reshape(1, 4))
    )
    inequality_rhs = np.concatenate(
        (
            np.zeros(4),
            np.full(4, max_weight),
            np.array([-min_expected_return]),
        )
    )

    budget_row = np.ones((1, 4))
    tolerance = np.sqrt(np.finfo(float).eps)
    candidates = []
    candidate_variances = []

    # The budget equality leaves at most three independent active inequalities.
    for active_count in range(4):
        for active_set in combinations(
            range(inequality_matrix.shape[0]), active_count
        ):
            if active_set:
                active_indices = list(active_set)
                equality_matrix = np.vstack(
                    (budget_row, inequality_matrix[active_indices, :])
                )
                equality_rhs = np.concatenate(
                    (
                        np.array([budget_sum]),
                        inequality_rhs[active_indices],
                    )
                )
            else:
                equality_matrix = budget_row
                equality_rhs = np.array([budget_sum])

            equality_count = equality_matrix.shape[0]
            kkt_matrix = np.block(
                [
                    [2.0 * covariance_matrix, equality_matrix.T],
                    [
                        equality_matrix,
                        np.zeros((equality_count, equality_count)),
                    ],
                ]
            )
            kkt_rhs = np.concatenate((np.zeros(4), equality_rhs))

            try:
                solution = np.linalg.solve(kkt_matrix, kkt_rhs)
            except np.linalg.LinAlgError:
                continue

            weights = solution[:4]
            if not np.all(np.isfinite(weights)):
                continue

            equality_scale = (
                1.0
                + np.abs(equality_rhs)
                + np.abs(equality_matrix) @ np.abs(weights)
            )
            if np.any(
                np.abs(equality_matrix @ weights - equality_rhs)
                > tolerance * equality_scale
            ):
                continue

            inequality_scale = (
                1.0
                + np.abs(inequality_rhs)
                + np.abs(inequality_matrix) @ np.abs(weights)
            )
            if np.any(
                inequality_matrix @ weights - inequality_rhs
                > tolerance * inequality_scale
            ):
                continue

            candidates.append(weights.copy())
            candidate_variances.append(
                float(weights @ covariance_matrix @ weights)
            )

    if not candidates:
        return {"objective": None, "status": "infeasible"}

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, 3)
    model.candidates = pyo.RangeSet(0, len(candidates) - 1)

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
        bounds=(0.0, max_weight),
    )
    model.selected = pyo.Var(model.candidates, domain=pyo.Binary)

    model.choose_candidate = pyo.Constraint(
        expr=sum(model.selected[candidate] for candidate in model.candidates)
        == 1
    )

    def link_weight_rule(instance, asset):
        return instance.weight[asset] == sum(
            float(candidates[candidate][asset])
            * instance.selected[candidate]
            for candidate in instance.candidates
        )

    model.link_weight = pyo.Constraint(
        model.assets, rule=link_weight_rule
    )
    model.budget_constraint = pyo.Constraint(
        expr=sum(model.weight[asset] for asset in model.assets) == budget_sum
    )
    model.return_constraint = pyo.Constraint(
        expr=sum(
            float(expected_returns[asset]) * model.weight[asset]
            for asset in model.assets
        )
        >= min_expected_return
    )
    model.portfolio_variance = pyo.Objective(
        expr=sum(
            candidate_variances[candidate] * model.selected[candidate]
            for candidate in model.candidates
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.portfolio_variance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}