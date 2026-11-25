# IR: {"sets":{"assets":[0,1,2,3,4]},"params":["expected_returns","min_return","max_weight","budget_sum_weights"],"decision_variables":{"weights[assets]":"nonnegative continuous"},"constraints":["sum(weights[i] for i in assets) == budget_sum_weights","sum(expected_returns[i]*weights[i] for i in assets) >= min_return","weights[i] <= max_weight for each i in assets"],"objective":{"sense":"minimize","expression":"sum(covariance[i,j]*weights[i]*weights[j] for i,j in assets)","defined":false},"missing_data":["covariance coefficients or an explicit portfolio-variance formula"]}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    max_weight = params["max_weight"]
    budget_sum_weights = params["budget_sum_weights"]

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, 4)

    model.asset_returns = pyo.Param(
        model.assets,
        initialize={idx: expected_returns[idx] for idx in model.assets},
    )
    model.required_return = pyo.Param(initialize=min_return)
    model.weight_cap = pyo.Param(initialize=max_weight)
    model.total_allocation = pyo.Param(initialize=budget_sum_weights)

    model.weights = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
    )

    model.allocation_constraint = pyo.Constraint(
        expr=sum(model.weights[idx] for idx in model.assets)
        == model.total_allocation
    )

    model.return_constraint = pyo.Constraint(
        expr=sum(
            model.asset_returns[idx] * model.weights[idx]
            for idx in model.assets
        )
        >= model.required_return
    )

    def weight_cap_rule(instance, idx):
        return instance.weights[idx] <= instance.weight_cap

    model.weight_cap_constraints = pyo.Constraint(
        model.assets,
        rule=weight_cap_rule,
    )

    # The supplied problem omits both the covariance coefficients and the
    # referenced quadratic variance constraint. Expected returns cannot
    # determine either asset variances or covariances.
    #
    # Consequently, a minimum-variance objective cannot be constructed from
    # these parameters. Calling Highs().solve(model) with an invented or
    # constant objective would solve a different problem. The earlier failure
    # requires additional problem data; it cannot be corrected in code alone.
    return {"objective": None, "status": "missing_covariance_data"}