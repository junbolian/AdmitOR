# IR: {"sets":{"assets":[0,1,2,3]},"params":["returns","min_return","weight_sum_target","weight_upper_bound","weight_lower_bound"],"variables":{"weight[assets]":"continuous in [weight_lower_bound, weight_upper_bound]"},"constraints":["sum(weight[i] for i in assets) == weight_sum_target","sum(returns[i]*weight[i] for i in assets) >= min_return"],"objective":{"sense":"minimize","expression":null,"reason":"The covariance matrix or equivalent quadratic variance expression is missing."},"on_missing_objective":{"objective":null,"status":"missing_variance_definition"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    returns = params["returns"]
    min_return = params["min_return"]
    weight_sum_target = params["weight_sum_target"]
    weight_upper_bound = params["weight_upper_bound"]
    weight_lower_bound = params["weight_lower_bound"]

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, 3)

    model.expected_returns = pyo.Param(
        model.assets,
        initialize={asset: returns[asset] for asset in model.assets},
    )
    model.required_return = pyo.Param(initialize=min_return)
    model.allocation_target = pyo.Param(initialize=weight_sum_target)
    model.allocation_lower_bound = pyo.Param(initialize=weight_lower_bound)
    model.allocation_upper_bound = pyo.Param(initialize=weight_upper_bound)

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.Reals,
        bounds=(
            model.allocation_lower_bound,
            model.allocation_upper_bound,
        ),
    )

    model.budget_constraint = pyo.Constraint(
        expr=sum(model.weight[asset] for asset in model.assets)
        == model.allocation_target
    )
    model.return_constraint = pyo.Constraint(
        expr=sum(
            model.expected_returns[asset] * model.weight[asset]
            for asset in model.assets
        )
        >= model.required_return
    )

    # The previous failure reflects missing problem data, not an implementation
    # defect. Portfolio variance requires covariance coefficients (or an
    # explicitly supplied equivalent quadratic expression). Expected returns
    # do not determine those coefficients.
    #
    # Consequently, no complete variance-minimization model can be constructed
    # from the specified params. Calling Highs().solve(model) and reporting an
    # objective here would require inventing the missing objective.
    return {"objective": None, "status": "missing_variance_definition"}