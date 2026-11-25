# IR: {"sets":{"assets":[0,1,2,3,4,5],"candidates":"vertices and interior segment minima derived from the allocation polytope"},"params":["expected_returns","min_expected_return","max_weight","covariance_0_1","covariance_0_2"],"derived":{"Q(w)":"2*w[0]*(covariance_0_1*w[1]+covariance_0_2*w[2])","candidate_weight[k,i]":"coordinates of candidate k","candidate_cost[k]":"Q(candidate_weight[k])"},"variables":{"weight[i]":"continuous, 0 <= weight[i] <= max_weight","choose[k]":"binary"},"constraints":["sum(weight[i]) == 1","sum(expected_returns[i]*weight[i]) >= min_expected_return","sum(choose[k]) == 1","weight[i] == sum(candidate_weight[k,i]*choose[k]) for each asset i"],"objective":"minimize sum(candidate_cost[k]*choose[k])"}
#
# Only the two supplied covariance terms are included. The other covariance
# entries and asset variances are unspecified, so this is the sparse objective
# defined by the available data, not an inferred full covariance matrix.
#
# Exact finite reformulation:
# For fixed weight[0], Q is linear in the other weights. An optimum therefore
# exists at a vertex of that slice, hence on an edge of the original allocation
# polytope. Enumerating all vertex pairs includes every edge. Minimizing Q on
# each such segment supplies a finite candidate set containing a global optimum.
# A binary selection model then permits the required Appsi HiGHS solve without
# passing an unsupported quadratic objective to that interface.

from itertools import combinations

import numpy as np
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    min_expected_return = float(params["min_expected_return"])
    max_weight = float(params["max_weight"])
    covariance_0_1 = float(params["covariance_0_1"])
    covariance_0_2 = float(params["covariance_0_2"])

    assets = tuple(range(6))
    returns = np.array(
        [float(expected_returns[asset]) for asset in assets], dtype=float
    )

    if not (
        np.all(np.isfinite(returns))
        and np.isfinite(min_expected_return)
        and np.isfinite(max_weight)
        and np.isfinite(covariance_0_1)
        and np.isfinite(covariance_0_2)
    ):
        return {"objective": None, "status": "invalid_parameters"}

    if max_weight < 0:
        return {"objective": None, "status": "infeasible"}

    # Allocation polytope: A @ weight <= b, sum(weight) == 1.
    identity = np.eye(len(assets))
    inequality_matrix = np.vstack((identity, -identity, -returns))
    inequality_rhs = np.concatenate(
        (
            np.full(len(assets), max_weight),
            np.zeros(len(assets)),
            np.array([-min_expected_return]),
        )
    )

    feasibility_tolerance = 1e-9
    duplicate_tolerance = 1e-10
    vertices = []

    # A vertex has five independent active inequalities in addition to
    # the allocation equality. Degenerate vertices may be discovered repeatedly.
    for active_rows in combinations(range(len(inequality_rhs)), len(assets) - 1):
        selected_rows = list(active_rows)
        equation_matrix = np.vstack(
            (np.ones(len(assets)), inequality_matrix[selected_rows])
        )
        equation_rhs = np.concatenate(
            (np.array([1.0]), inequality_rhs[selected_rows])
        )

        try:
            point = np.linalg.solve(equation_matrix, equation_rhs)
        except np.linalg.LinAlgError:
            continue

        residuals = inequality_matrix @ point - inequality_rhs
        scales = 1.0 + np.abs(inequality_rhs)
        if np.any(residuals > feasibility_tolerance * scales):
            continue

        if any(
            np.max(np.abs(point - existing)) <= duplicate_tolerance
            for existing in vertices
        ):
            continue

        vertices.append(point)

    def portfolio_cost(point):
        return float(
            2.0
            * point[0]
            * (
                covariance_0_1 * point[1]
                + covariance_0_2 * point[2]
            )
        )

    candidates = list(vertices)

    for first, second in combinations(vertices, 2):
        direction = second - first
        linear_at_first = (
            covariance_0_1 * first[1] + covariance_0_2 * first[2]
        )
        linear_direction = (
            covariance_0_1 * direction[1]
            + covariance_0_2 * direction[2]
        )

        # Q(first + t*direction) = constant + linear*t + quadratic*t**2.
        quadratic = 2.0 * direction[0] * linear_direction
        linear = 2.0 * (
            first[0] * linear_direction
            + direction[0] * linear_at_first
        )

        if quadratic > 0.0:
            fraction = -linear / (2.0 * quadratic)
            if 0.0 < fraction < 1.0:
                candidates.append(first + fraction * direction)

    model = pyo.ConcreteModel()
    model.assets = pyo.Set(initialize=assets, ordered=True)
    model.candidates = pyo.Set(
        initialize=range(len(candidates)), ordered=True
    )

    model.asset_return = pyo.Param(
        model.assets,
        initialize={asset: returns[asset] for asset in assets},
    )
    model.return_requirement = pyo.Param(initialize=min_expected_return)
    model.allocation_limit = pyo.Param(initialize=max_weight)

    model.candidate_weight = pyo.Param(
        model.candidates,
        model.assets,
        initialize={
            (candidate, asset): float(candidates[candidate][asset])
            for candidate in range(len(candidates))
            for asset in assets
        },
    )
    model.candidate_cost = pyo.Param(
        model.candidates,
        initialize={
            candidate: portfolio_cost(candidates[candidate])
            for candidate in range(len(candidates))
        },
    )

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
        bounds=(0.0, max_weight),
    )
    model.choose = pyo.Var(model.candidates, domain=pyo.Binary)

    model.total_allocation = pyo.Constraint(
        expr=sum(model.weight[asset] for asset in model.assets) == 1.0
    )
    model.required_return = pyo.Constraint(
        expr=sum(
            model.asset_return[asset] * model.weight[asset]
            for asset in model.assets
        ) >= model.return_requirement
    )

    # The symbolic zero also keeps an empty candidate set valid Pyomo syntax;
    # in that case this constraint correctly makes the model infeasible.
    model.single_candidate = pyo.Constraint(
        expr=sum(
            (model.choose[candidate] for candidate in model.candidates),
            0.0 * model.weight[0],
        ) == 1.0
    )

    def candidate_link_rule(mdl, asset):
        return mdl.weight[asset] == sum(
            mdl.candidate_weight[candidate, asset] * mdl.choose[candidate]
            for candidate in mdl.candidates
        )

    model.candidate_link = pyo.Constraint(
        model.assets, rule=candidate_link_rule
    )
    model.portfolio_variance = pyo.Objective(
        expr=sum(
            (
                model.candidate_cost[candidate] * model.choose[candidate]
                for candidate in model.candidates
            ),
            0.0 * model.weight[0],
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.portfolio_variance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}