# IR: {"sets":{"assets":[0,1,2,3,4,5]},"params":["expected_returns","min_return","max_weight","budget","cov_0_1","cov_0_2","covariance_scale"],"decision_variables":{"weight[i]":{"type":"continuous","bounds":"[0,max_weight]"}},"constraints":["sum(weight[i] for i in assets) == budget","sum(expected_returns[i]*weight[i] for i in assets) >= min_return"],"objective":{"sense":"minimize","expression":"sum(covariance[i,j]*weight[i]*weight[j] for i,j in assets)"},"preconditions":["The six diagonal and thirteen remaining upper-triangular covariance baseline coefficients must be supplied.","The solver interface must support the quadratic objective."],"on_unmet_precondition":{"objective":null,"status":"incomplete_problem_specification"}}

# A corrected optimizer cannot be derived from the supplied specification:
# covariance_scale supplies a multiplier, not the nineteen missing baseline
# coefficients. Different baseline matrices give different optimal objectives.
# The example expected returns cannot determine those coefficients.
#
# Independently, the required pyomo.contrib.appsi.solvers.highs.Highs
# interface does not support quadratic objectives. Native HiGHS QP support
# does not make that particular Pyomo interface QP-capable.
#
# Returning an "optimal" objective would therefore require inventing data or
# changing the requested mathematical problem or solver interface. The
# previous missing-data result reflects missing inputs, not a coding defect.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    max_weight = params["max_weight"]
    budget = params["budget"]
    cov_0_1 = params["cov_0_1"]
    cov_0_2 = params["cov_0_2"]
    covariance_scale = params["covariance_scale"]

    return {
        "objective": None,
        "status": "incomplete_problem_specification",
    }