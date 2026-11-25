# IR: {"sets":{"assets":[0,1,2,3]},"params":["expected_return_asset0","expected_return_asset1","expected_return_asset2","expected_return_asset3","min_portfolio_return","budget_sum","max_asset_weight","min_asset_weight"],"decision_variables":{"weight[assets]":{"type":"continuous","bounds":["min_asset_weight","max_asset_weight"]}},"constraints":["sum(weight[i] for i in assets) == budget_sum","sum(expected_return_asset[i] * weight[i] for i in assets) >= min_portfolio_return"],"objective":null,"outcome":{"objective":null,"status":"missing_variance_definition"}}
#
# The supplied problem is mathematically incomplete: neither a covariance
# matrix nor the quadratic variance expression is specified. Expected returns
# do not determine those missing coefficients.
#
# A corrected variance-minimization solve cannot be implemented from these
# inputs alone. Inventing a covariance matrix, minimizing squared weights,
# or introducing an unconstrained variance variable changes the problem.
# This function builds exactly the specified portion and reports the missing
# definition instead of reporting an unrelated objective as optimal.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = {
        0: params["expected_return_asset0"],
        1: params["expected_return_asset1"],
        2: params["expected_return_asset2"],
        3: params["expected_return_asset3"],
    }
    minimum_return = params["min_portfolio_return"]
    total_budget = params["budget_sum"]
    maximum_weight = params["max_asset_weight"]
    minimum_weight = params["min_asset_weight"]

    model = pyo.ConcreteModel()
    model.assets = pyo.Set(initialize=range(4), ordered=True)

    model.expected_return = pyo.Param(
        model.assets, initialize=expected_returns
    )
    model.minimum_return = pyo.Param(initialize=minimum_return)
    model.total_budget = pyo.Param(initialize=total_budget)
    model.maximum_weight = pyo.Param(initialize=maximum_weight)
    model.minimum_weight = pyo.Param(initialize=minimum_weight)

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.Reals,
        bounds=(model.minimum_weight, model.maximum_weight),
    )

    model.budget_constraint = pyo.Constraint(
        expr=sum(model.weight[i] for i in model.assets)
        == model.total_budget
    )
    model.return_constraint = pyo.Constraint(
        expr=sum(
            model.expected_return[i] * model.weight[i]
            for i in model.assets
        )
        >= model.minimum_return
    )

    # There is no specified objective component to solve or evaluate.
    # Calling Highs here would not solve the requested variance problem.
    return {"objective": None, "status": "missing_variance_definition"}