# IR: {"sets":{"assets":[0,1,2,3]},"params":["expected_return_asset0","expected_return_asset1","expected_return_asset2","expected_return_asset3","min_portfolio_return","budget_sum","max_asset_weight","min_asset_weight"],"variables":{"weight[assets]":"continuous, bounded by min_asset_weight and max_asset_weight"},"constraints":["sum(weight[i] for i in assets) == budget_sum","sum(expected_return_asset[i]*weight[i] for i in assets) >= min_portfolio_return"],"objective":{"sense":"minimize","expression":null,"missing":"Quadratic variance expression or covariance matrix"},"failure_status":"missing_variance_definition"}

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
    total_weight = params["budget_sum"]
    maximum_weight = params["max_asset_weight"]
    minimum_weight = params["min_asset_weight"]

    model = pyo.ConcreteModel()
    model.assets = pyo.Set(initialize=range(4), ordered=True)
    model.weight = pyo.Var(
        model.assets,
        domain=pyo.Reals,
        bounds=(minimum_weight, maximum_weight),
    )
    model.budget_constraint = pyo.Constraint(
        expr=sum(model.weight[asset] for asset in model.assets) == total_weight
    )
    model.return_constraint = pyo.Constraint(
        expr=sum(
            expected_returns[asset] * model.weight[asset]
            for asset in model.assets
        )
        >= minimum_return
    )

    # The previous failure identifies missing problem data, not a coding error.
    # Portfolio variance requires a specified quadratic expression, typically
    # sum(covariance[i, j] * weight[i] * weight[j] for i, j).
    # Neither that expression nor its coefficients appear in the problem or
    # PARAMS. Expected returns do not determine covariances.
    #
    # Consequently, no variance objective can be constructed or retrieved.
    # Calling Highs().solve(model) on this incomplete model would not solve
    # the requested optimization problem. Substituting equal variances,
    # independent assets, or a constant objective would invent assumptions.
    return {"objective": None, "status": "missing_variance_definition"}