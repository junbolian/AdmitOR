# IR: {"sets":{"assets":[0,1,2,3,4,5,6,7]},"params":["expected_returns","min_return","budget","max_weight"],"variables":{"weight":{"index":"assets","type":"nonnegative continuous"}},"constraints":["sum(weight[i] for i in assets) == budget","sum(expected_returns[i]*weight[i] for i in assets) >= min_return","weight[i] <= max_weight for i in assets"],"objective":{"sense":"minimize","expression":null,"reason":"Portfolio variance requires asset variances and covariances, which are not supplied."}}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    budget = params["budget"]
    max_weight = params["max_weight"]

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, 7)

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
        bounds=(0, max_weight),
    )

    model.budget_constraint = pyo.Constraint(
        expr=sum(model.weight[asset_id] for asset_id in model.assets)
        == budget
    )

    model.return_constraint = pyo.Constraint(
        expr=sum(
            expected_returns[asset_id] * model.weight[asset_id]
            for asset_id in model.assets
        )
        >= min_return
    )

    # No mathematically valid correction can produce the requested optimum
    # from the supplied parameters. Portfolio variance is w.T @ covariance @ w;
    # expected returns do not determine the covariance matrix. Assuming an
    # identity matrix, zero covariances, or any other risk model would introduce
    # information absent from the problem and change the optimization task.
    #
    # A covariance matrix must be supplied before a risk objective can be
    # defined. Furthermore, the mandated Pyomo APPSI Highs interface does not
    # directly support the quadratic objective/constraint formulation described.
    #
    # Calling Highs().solve(model) and reporting a retrieved feasibility
    # objective as portfolio variance would therefore misrepresent the result.
    return {"objective": None, "status": "missing_covariance_matrix"}