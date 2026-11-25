# IR: {"sets":{"assets":[0,1,2,3],"pairs":[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]]},"params":{"expected_return":["expected_return_0","expected_return_1","expected_return_2","expected_return_3"],"variance":["variance_0","variance_1","variance_2","variance_3"],"covariance":["covariance_01","covariance_02","covariance_03","covariance_12","covariance_13","covariance_23"],"scalars":["min_return","sum_weights","max_weight"]},"variables":{"weight[i]":{"type":"continuous","lower":0,"upper":"max_weight"}},"constraints":["sum(weight[i] for i in assets) == sum_weights","sum(expected_return[i]*weight[i] for i in assets) >= min_return"],"objective":{"sense":"minimize","expression":"sum(variance[i]*weight[i]**2 for i in assets) + 2*sum(covariance[i,j]*weight[i]*weight[j] for (i,j) in pairs)"}}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs
from pyomo.contrib.appsi.solvers.highs import DegreeError


def solve(params):
    expected_returns = {
        0: params["expected_return_0"],
        1: params["expected_return_1"],
        2: params["expected_return_2"],
        3: params["expected_return_3"],
    }
    variances = {
        0: params["variance_0"],
        1: params["variance_1"],
        2: params["variance_2"],
        3: params["variance_3"],
    }
    covariances = {
        (0, 1): params["covariance_01"],
        (0, 2): params["covariance_02"],
        (0, 3): params["covariance_03"],
        (1, 2): params["covariance_12"],
        (1, 3): params["covariance_13"],
        (2, 3): params["covariance_23"],
    }

    model = pyo.ConcreteModel()
    model.assets = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.pairs = pyo.Set(
        dimen=2,
        initialize=[(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)],
        ordered=True,
    )

    model.expected_return = pyo.Param(
        model.assets, initialize=expected_returns
    )
    model.variance = pyo.Param(model.assets, initialize=variances)
    model.covariance = pyo.Param(model.pairs, initialize=covariances)
    model.minimum_return = pyo.Param(initialize=params["min_return"])
    model.total_allocation = pyo.Param(initialize=params["sum_weights"])
    model.allocation_cap = pyo.Param(initialize=params["max_weight"])

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
        bounds=(0, model.allocation_cap),
    )

    model.allocation_balance = pyo.Constraint(
        expr=sum(model.weight[i] for i in model.assets)
        == model.total_allocation
    )
    model.return_requirement = pyo.Constraint(
        expr=sum(
            model.expected_return[i] * model.weight[i]
            for i in model.assets
        )
        >= model.minimum_return
    )

    model.portfolio_variance = pyo.Objective(
        expr=(
            sum(
                model.variance[i] * model.weight[i] ** 2
                for i in model.assets
            )
            + 2
            * sum(
                model.covariance[i, j] * model.weight[i] * model.weight[j]
                for i, j in model.pairs
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except DegreeError:
        return {
            "objective": None,
            "status": "unsupported_quadratic_objective",
        }
    except ApplicationError:
        return {"objective": None, "status": "solver_failed"}
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.portfolio_variance))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}