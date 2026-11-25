# IR: {"sets":{"assets":"0..7"},"params":{"min_return":"params['min_return']","max_weight":"params['max_weight']","budget":"params['budget']","expected_returns":"params['expected_returns']; required but not supplied","covariance":"params['covariance']; required but not supplied"},"variables":{"weight[i]":"continuous; 0 <= weight[i] <= max_weight"},"constraints":["sum(weight[i] for i in assets) == budget","sum(expected_returns[i]*weight[i] for i in assets) >= min_return"],"objective":"minimize sum(covariance[i][j]*weight[i]*weight[j] for i,j in assets)"}

# The previous failure cannot be corrected from the supplied data:
# min_return, max_weight, and budget do not determine the eight expected
# returns or the covariance matrix. Inventing those coefficients would
# change the problem.
#
# There is also an independent interface limitation: Pyomo's APPSI Highs
# interface rejects quadratic objectives. This script reports either
# limitation explicitly rather than returning a fabricated optimum.
# A successful implementation requires the missing coefficients and a
# solver interface that supports quadratic objectives.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs, DegreeError


def solve(params):
    min_return = params["min_return"]
    max_weight = params["max_weight"]
    budget = params["budget"]

    if "expected_returns" not in params or "covariance" not in params:
        return {"objective": None, "status": "missing_portfolio_data"}

    expected_returns = params["expected_returns"]
    covariance = params["covariance"]

    if len(expected_returns) != 8:
        return {"objective": None, "status": "invalid_return_dimensions"}
    if len(covariance) != 8 or any(len(row) != 8 for row in covariance):
        return {"objective": None, "status": "invalid_covariance_dimensions"}

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, 7)

    model.required_return = pyo.Param(initialize=min_return)
    model.weight_limit = pyo.Param(initialize=max_weight)
    model.total_budget = pyo.Param(initialize=budget)
    model.asset_returns = pyo.Param(
        model.assets,
        initialize={i: expected_returns[i] for i in range(8)},
    )
    model.asset_covariance = pyo.Param(
        model.assets,
        model.assets,
        initialize={
            (i, j): covariance[i][j]
            for i in range(8)
            for j in range(8)
        },
    )

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
        bounds=(0, model.weight_limit),
    )

    model.budget_constraint = pyo.Constraint(
        expr=sum(model.weight[i] for i in model.assets) == model.total_budget
    )
    model.return_constraint = pyo.Constraint(
        expr=sum(
            model.asset_returns[i] * model.weight[i]
            for i in model.assets
        ) >= model.required_return
    )
    model.portfolio_variance = pyo.Objective(
        expr=sum(
            model.asset_covariance[i, j] * model.weight[i] * model.weight[j]
            for i in model.assets
            for j in model.assets
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except DegreeError:
        return {"objective": None, "status": "unsupported_quadratic_objective"}
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.portfolio_variance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}