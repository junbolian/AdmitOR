# IR: {"sets":{"assets":"0..9"},"params":["expected_returns","max_allocation","total_allocation","min_return","covariance_0_1","covariance_0_2"],"decision_variables":{"weight[i]":"continuous; 0 <= weight[i] <= max_allocation","variance":"continuous"},"constraints":["sum(weight[i]) == total_allocation","sum(expected_returns[i]*weight[i]) >= min_return","variance == sum(Sigma[i,j]*weight[i]*weight[j] for i,j in assets); requires the full covariance matrix"],"objective":"minimize variance","validation":["Reject scalar expected_returns: ten individual returns are required.","Return missing_covariance_data when the full covariance matrix is unavailable."],"execution":"Validation fails before model construction because PARAMS does not specify the full covariance matrix."}

from collections.abc import Mapping
from numbers import Real

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    max_allocation = params["max_allocation"]
    total_allocation = params["total_allocation"]
    min_return = params["min_return"]
    covariance_0_1 = params["covariance_0_1"]
    covariance_0_2 = params["covariance_0_2"]

    # A scalar cannot specify ten individual asset returns. Reject it
    # explicitly instead of indexing it or silently inventing returns.
    if isinstance(expected_returns, (Real, str, bytes)):
        return {"objective": None, "status": "invalid_expected_returns"}

    if isinstance(expected_returns, Mapping):
        if all(asset in expected_returns for asset in range(10)):
            asset_returns = [
                expected_returns[asset] for asset in range(10)
            ]
        elif all(str(asset) in expected_returns for asset in range(10)):
            asset_returns = [
                expected_returns[str(asset)] for asset in range(10)
            ]
        else:
            return {"objective": None, "status": "invalid_expected_returns"}
    else:
        try:
            asset_returns = list(expected_returns)
        except TypeError:
            return {"objective": None, "status": "invalid_expected_returns"}

        if len(asset_returns) != 10:
            return {"objective": None, "status": "invalid_expected_returns"}

    # The two supplied covariances do not determine portfolio variance.
    # All ten individual variances and the other pairwise covariances
    # remain unspecified. Assuming values for them would change the problem.
    #
    # Consequently, no complete model can be constructed or submitted to
    # Highs().solve(model), and no objective can legitimately be retrieved.
    # A full covariance matrix is required to implement the stated IR.
    return {"objective": None, "status": "missing_covariance_data"}