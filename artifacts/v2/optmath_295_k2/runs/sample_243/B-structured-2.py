# IR: {"sets":{"A":"0..9"},"params":{"expected_returns":"vector[A]","max_allocation":"scalar","total_allocation":"scalar","min_return":"scalar","covariance_0_1":"scalar","covariance_0_2":"scalar","covariance_matrix":"additional required 10x10 matrix; the two specified covariances override corresponding symmetric entries"},"variables":{"weight[A]":"nonnegative continuous","portfolio_variance":"continuous"},"constraints":["weight[i] <= max_allocation for i in A","sum(weight[i] for i in A) == total_allocation","sum(expected_returns[i]*weight[i] for i in A) >= min_return","portfolio_variance == sum(covariance[i,j]*weight[i]*weight[j] for i,j in A)"],"objective":"minimize portfolio_variance","failure_conditions":["missing covariance_matrix: insufficient_covariance_data","unsupported quadratic expressions: unsupported_quadratic_model","solver RuntimeError: solver_failed","objective cannot be evaluated: objective_unavailable"]}

import pyomo.environ as pyo
from pyomo.contrib.appsi.base import DegreeError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # The six listed inputs do not specify asset variances or the remaining
    # covariances. A complete covariance matrix is required to determine risk.
    # The APPSI HiGHS interface also rejects the quadratic equality below;
    # report that limitation instead of changing the optimization problem.

    expected_returns = params["expected_returns"]
    max_allocation = params["max_allocation"]
    total_allocation = params["total_allocation"]
    min_return = params["min_return"]
    covariance_0_1 = params["covariance_0_1"]
    covariance_0_2 = params["covariance_0_2"]

    if "covariance_matrix" not in params:
        return {"objective": None, "status": "insufficient_covariance_data"}

    covariance_matrix = params["covariance_matrix"]
    asset_indices = range(10)

    covariance_data = {
        (asset_i, asset_j): covariance_matrix[asset_i][asset_j]
        for asset_i in asset_indices
        for asset_j in asset_indices
    }
    covariance_data[0, 1] = covariance_0_1
    covariance_data[1, 0] = covariance_0_1
    covariance_data[0, 2] = covariance_0_2
    covariance_data[2, 0] = covariance_0_2

    model = pyo.ConcreteModel()
    model.assets = pyo.Set(initialize=asset_indices, ordered=True)

    model.asset_return = pyo.Param(
        model.assets,
        initialize={
            asset_i: expected_returns[asset_i]
            for asset_i in asset_indices
        },
        within=pyo.Reals,
    )
    model.allocation_limit = pyo.Param(
        initialize=max_allocation,
        within=pyo.Reals,
    )
    model.allocation_target = pyo.Param(
        initialize=total_allocation,
        within=pyo.Reals,
    )
    model.return_requirement = pyo.Param(
        initialize=min_return,
        within=pyo.Reals,
    )
    model.asset_covariance = pyo.Param(
        model.assets,
        model.assets,
        initialize=covariance_data,
        within=pyo.Reals,
    )

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
    )
    model.portfolio_variance = pyo.Var(domain=pyo.Reals)

    model.allocation_caps = pyo.Constraint(
        model.assets,
        rule=lambda portfolio, asset_i: (
            portfolio.weight[asset_i] <= portfolio.allocation_limit
        ),
    )
    model.allocation_balance = pyo.Constraint(
        expr=sum(model.weight[asset_i] for asset_i in model.assets)
        == model.allocation_target
    )
    model.minimum_expected_return = pyo.Constraint(
        expr=sum(
            model.asset_return[asset_i] * model.weight[asset_i]
            for asset_i in model.assets
        )
        >= model.return_requirement
    )
    model.variance_definition = pyo.Constraint(
        expr=model.portfolio_variance
        == sum(
            model.asset_covariance[asset_i, asset_j]
            * model.weight[asset_i]
            * model.weight[asset_j]
            for asset_i in model.assets
            for asset_j in model.assets
        )
    )
    model.risk_objective = pyo.Objective(
        expr=model.portfolio_variance,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except DegreeError:
        return {"objective": None, "status": "unsupported_quadratic_model"}
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.risk_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}