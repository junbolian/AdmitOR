# IR: {"sets":{"assets":[0,1,2,3,4,5]},"params":["expected_returns","min_expected_return","max_weight","covariance_0_1","covariance_0_2"],"decision_variables":{"weight[assets]":{"type":"continuous","bounds":[0,"max_weight"]}},"constraints":["sum(weight[i] for i in assets) == 1","sum(expected_returns[i]*weight[i] for i in assets) >= min_expected_return"],"objective":{"sense":"minimize","expression":"sum(covariance[i,j]*weight[i]*weight[j] for i,j in assets)","availability":"undefined: the supplied parameters do not specify the full covariance matrix"},"failure_status":"incomplete_covariance"}
#
# No exact optimization script can satisfy all the stated requirements:
# - The asset variances and remaining covariances are unspecified. Treating
#   them as zero would invent data and change the portfolio problem.
# - Even with a complete covariance matrix, the requested Pyomo APPSI
#   HiGHS interface does not accept quadratic objectives. McCormick
#   inequalities alone would provide a relaxation, not an exact solution.
#
# This script builds the specified feasible region and reports the missing
# objective data rather than returning a fabricated optimal variance.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    min_expected_return = params["min_expected_return"]
    max_weight = params["max_weight"]
    covariance_0_1 = params["covariance_0_1"]
    covariance_0_2 = params["covariance_0_2"]

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, 5)

    model.asset_return = pyo.Param(
        model.assets,
        initialize={
            asset: expected_returns[asset]
            for asset in model.assets
        },
    )
    model.required_return = pyo.Param(initialize=min_expected_return)
    model.allocation_limit = pyo.Param(initialize=max_weight)

    model.supplied_covariance_pairs = pyo.Set(
        dimen=2,
        initialize=[(0, 1), (0, 2)],
    )
    model.supplied_covariance = pyo.Param(
        model.supplied_covariance_pairs,
        initialize={
            (0, 1): covariance_0_1,
            (0, 2): covariance_0_2,
        },
    )

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
        bounds=(0, max_weight),
    )
    model.total_allocation = pyo.Constraint(
        expr=sum(model.weight[asset] for asset in model.assets) == 1
    )
    model.return_requirement = pyo.Constraint(
        expr=sum(
            model.asset_return[asset] * model.weight[asset]
            for asset in model.assets
        ) >= model.required_return
    )

    # No objective or solver call is valid for the unspecified variance.
    return {"objective": None, "status": "incomplete_covariance"}