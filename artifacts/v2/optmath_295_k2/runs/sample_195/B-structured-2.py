# IR: {"sets":{"A":[0,1,2,3],"P":[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]],"C":"Feasible stationary points obtained by enumerating independent active constraint sets, always including the budget equality."},"params":{"expected_returns":"length-4 sequence","min_expected_return":"scalar","variances":"length-4 sequence","covariances":"length-6 sequence ordered as P","max_weight":"scalar","budget_sum":"scalar"},"derived":{"Q":"Symmetric covariance matrix with diagonal variances and off-diagonal covariances.","candidate[c]":"Solve the equality-constrained stationarity system for each active set with at most three additional constraints; retain feasible solutions of nonsingular systems.","risk[c]":"candidate[c]^T Q candidate[c]","weight[a]":"sum(candidate[c][a]*mix[c] for c in C)"},"variables":{"mix[C]":"nonnegative continuous"},"constraints":["sum(mix[c] for c in C) == 1","sum(weight[a] for a in A) == budget_sum","sum(expected_returns[a]*weight[a] for a in A) >= min_expected_return","0 <= weight[a] <= max_weight for a in A"],"objective":"minimize sum(risk[c]*mix[c] for c in C); this finite-candidate LP has the same optimal value as the original quadratic portfolio problem."}

from itertools import combinations

import numpy as np
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = np.asarray(
        params["expected_returns"], dtype=float
    )
    min_expected_return = float(params["min_expected_return"])
    variances = np.asarray(params["variances"], dtype=float)
    covariances = np.asarray(params["covariances"], dtype=float)
    max_weight = float(params["max_weight"])
    budget_sum = float(params["budget_sum"])

    assets = tuple(range(4))
    pairs = (
        (0, 1), (0, 2), (0, 3),
        (1, 2), (1, 3), (2, 3),
    )

    if expected_returns.shape != (4,):
        raise ValueError("expected_returns must contain four values.")
    if variances.shape != (4,):
        raise ValueError("variances must contain four values.")
    if covariances.shape != (6,):
        raise ValueError("covariances must contain six values.")

    scalar_inputs = np.array(
        [min_expected_return, max_weight, budget_sum],
        dtype=float,
    )
    if not all(
        np.all(np.isfinite(values))
        for values in (
            expected_returns, variances, covariances, scalar_inputs
        )
    ):
        raise ValueError("All parameters must be finite.")

    covariance_matrix = np.diag(variances)
    for position, (first, second) in enumerate(pairs):
        covariance_matrix[first, second] = covariances[position]
        covariance_matrix[second, first] = covariances[position]

    # APPSI HiGHS accepts linear objectives. Enumerate the stationary
    # candidates first, then let HiGHS select the minimum-risk candidate.
    #
    # This also handles indefinite covariance matrices. A global minimum
    # exists on the bounded feasible polytope. Choose a minimizing face
    # of smallest dimension. Its reduced Hessian must be nonsingular:
    # otherwise a flat direction reaches a smaller minimizing face.
    # Thus at least one global minimizer occurs among these candidates.
    hessian = 2.0 * covariance_matrix
    unit_vectors = np.eye(4)

    active_boundaries = []
    for asset in assets:
        active_boundaries.append((unit_vectors[asset], 0.0))
        active_boundaries.append((unit_vectors[asset], max_weight))
    active_boundaries.append(
        (expected_returns.copy(), min_expected_return)
    )

    candidates = []

    if max_weight >= 0.0:
        for active_count in range(4):
            for selected_boundaries in combinations(
                active_boundaries, active_count
            ):
                equality_matrix = np.vstack(
                    [np.ones(4)]
                    + [boundary[0] for boundary in selected_boundaries]
                )
                equality_rhs = np.array(
                    [budget_sum]
                    + [boundary[1] for boundary in selected_boundaries],
                    dtype=float,
                )
                equality_count = equality_matrix.shape[0]

                stationarity_matrix = np.block([
                    [hessian, equality_matrix.T],
                    [
                        equality_matrix,
                        np.zeros((equality_count, equality_count)),
                    ],
                ])
                stationarity_rhs = np.concatenate(
                    [np.zeros(4), equality_rhs]
                )

                try:
                    stationary_solution = np.linalg.solve(
                        stationarity_matrix, stationarity_rhs
                    )
                except np.linalg.LinAlgError:
                    continue

                weights = stationary_solution[:4]
                if not np.all(np.isfinite(weights)):
                    continue

                # These tolerances only accommodate floating-point
                # linear algebra; the LP below retains the constraints.
                weight_tolerance = 1e-9 * (
                    1.0 + abs(budget_sum) + abs(max_weight)
                )
                return_tolerance = 1e-9 * (
                    1.0
                    + abs(min_expected_return)
                    + float(np.dot(
                        np.abs(expected_returns), np.abs(weights)
                    ))
                )

                if np.any(weights < -weight_tolerance):
                    continue
                if np.any(weights > max_weight + weight_tolerance):
                    continue
                if abs(float(weights.sum()) - budget_sum) > weight_tolerance:
                    continue
                if (
                    float(expected_returns @ weights)
                    < min_expected_return - return_tolerance
                ):
                    continue

                risk = float(
                    weights @ covariance_matrix @ weights
                )
                if not np.isfinite(risk):
                    raise ArithmeticError(
                        "Portfolio variance evaluation overflowed."
                    )

                candidates.append((weights.copy(), risk))

    model = pyo.ConcreteModel()

    model.assets = pyo.Set(initialize=assets, ordered=True)
    model.candidates = pyo.Set(
        initialize=range(len(candidates)), ordered=True
    )
    model.mix = pyo.Var(
        model.candidates, domain=pyo.NonNegativeReals
    )

    model.portfolio_weight = pyo.Expression(
        model.assets,
        rule=lambda mdl, asset: pyo.quicksum(
            float(candidates[candidate_id][0][asset])
            * mdl.mix[candidate_id]
            for candidate_id in mdl.candidates
        ),
    )

    # Tuple constraints remain valid Pyomo expressions even when the
    # candidate set is empty, in which case this LP is infeasible.
    model.mixture_total = pyo.Constraint(
        expr=(
            1.0,
            pyo.quicksum(
                model.mix[candidate_id]
                for candidate_id in model.candidates
            ),
            1.0,
        )
    )
    model.budget_requirement = pyo.Constraint(
        expr=(
            budget_sum,
            pyo.quicksum(
                model.portfolio_weight[asset]
                for asset in model.assets
            ),
            budget_sum,
        )
    )
    model.return_requirement = pyo.Constraint(
        expr=(
            min_expected_return,
            pyo.quicksum(
                float(expected_returns[asset])
                * model.portfolio_weight[asset]
                for asset in model.assets
            ),
            None,
        )
    )
    model.allocation_bounds = pyo.Constraint(
        model.assets,
        rule=lambda mdl, asset: (
            0.0, mdl.portfolio_weight[asset], max_weight
        ),
    )
    model.portfolio_variance = pyo.Objective(
        expr=pyo.quicksum(
            candidates[candidate_id][1] * model.mix[candidate_id]
            for candidate_id in model.candidates
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.portfolio_variance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}