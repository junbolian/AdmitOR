# IR: {"sets":{"assets":"0..9"},"params":{"expected_return":"10-vector from params","portfolio_return_min":"scalar from params","weight_sum_target":"scalar from params","weight_upper_bound":"scalar from params","weight_lower_bound":"scalar from params"},"variables":{"weight[i]":"continuous in [weight_lower_bound, weight_upper_bound]"},"constraints":["sum(weight[i]) == weight_sum_target","sum(expected_return[i]*weight[i]) >= portfolio_return_min"],"objective":{"sense":"minimize","expression":"sum(covariance[i,j]*weight[i]*weight[j])","missing_input":"covariance matrix or equivalent quadratic expression"},"result_if_missing_input":{"objective":null,"status":"missing_covariance"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_return = params["expected_return"]
    portfolio_return_min = params["portfolio_return_min"]
    weight_sum_target = params["weight_sum_target"]
    weight_upper_bound = params["weight_upper_bound"]
    weight_lower_bound = params["weight_lower_bound"]

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, 9)

    model.asset_returns = pyo.Param(
        model.assets,
        initialize={
            asset: expected_return[asset]
            for asset in model.assets
        },
    )
    model.required_return = pyo.Param(initialize=portfolio_return_min)
    model.total_weight_target = pyo.Param(initialize=weight_sum_target)
    model.minimum_weight = pyo.Param(initialize=weight_lower_bound)
    model.maximum_weight = pyo.Param(initialize=weight_upper_bound)

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.Reals,
        bounds=(model.minimum_weight, model.maximum_weight),
    )

    model.allocation_sum = pyo.Constraint(
        expr=sum(model.weight[asset] for asset in model.assets)
        == model.total_weight_target
    )
    model.return_requirement = pyo.Constraint(
        expr=sum(
            model.asset_returns[asset] * model.weight[asset]
            for asset in model.assets
        )
        >= model.required_return
    )

    # The previous failure cannot be corrected from the supplied inputs:
    # expected returns do not determine variances or covariances, and the
    # referenced quadratic LP expression is not included in the question.
    # Inventing an identity covariance matrix, minimizing squared weights,
    # or solving only these feasibility constraints would change the problem.
    #
    # Furthermore, Pyomo's APPsi Highs interface does not support quadratic
    # objectives. Even after supplying covariances, the prescribed interface
    # would require a separately justified reformulation or a changed solver.
    #
    # No objective value can honestly be reported for the stated problem.
    return {"objective": None, "status": "missing_covariance"}