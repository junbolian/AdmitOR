# IR: {"sets":{"assets":[0,1,2,3,4]},"params":{"expected_returns":"params[\"expected_returns\"]","min_return":"params[\"min_return\"]","budget":"params[\"budget\"]","max_weight":"params[\"max_weight\"]"},"variables":{"weight[i]":"continuous; 0 <= weight[i] <= max_weight"},"constraints":["sum(weight[i] for i in assets) == budget","sum(expected_returns[i]*weight[i] for i in assets) >= min_return"],"objective":{"sense":"minimize","expression":"sum(covariance[i,j]*weight[i]*weight[j] for i,j in assets)","unavailable":"Covariance coefficients are not provided."},"failure":{"objective":null,"status":"missing_covariance"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Build the specified constraints and report unavailable objective data.

    The previous failure cannot be corrected from the supplied information.
    Neither the covariance matrix nor the referenced quadratic constraint
    is supplied. Expected returns do not determine covariance coefficients.
    Substituting invented coefficients would solve a different problem.
    """
    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    budget = params["budget"]
    max_weight = params["max_weight"]

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, 4)

    model.asset_returns = pyo.Param(
        model.assets,
        initialize=lambda instance, asset: expected_returns[asset],
    )
    model.required_return = pyo.Param(initialize=min_return)
    model.total_budget = pyo.Param(initialize=budget)
    model.weight_limit = pyo.Param(initialize=max_weight)

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
        bounds=lambda instance, asset: (0, instance.weight_limit),
    )

    model.budget_constraint = pyo.Constraint(
        expr=sum(model.weight[asset] for asset in model.assets)
        == model.total_budget
    )
    model.return_constraint = pyo.Constraint(
        expr=sum(
            model.asset_returns[asset] * model.weight[asset]
            for asset in model.assets
        )
        >= model.required_return
    )

    # A variance objective cannot be defined without covariance coefficients.
    # Calling Highs().solve(model) on these constraints alone would not solve
    # the requested minimum-variance portfolio problem or justify "optimal".
    return {"objective": None, "status": "missing_covariance"}