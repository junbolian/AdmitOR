import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    assets = [0, 1, 2, 3]
    model.Assets = pyo.Set(initialize=assets)

    min_w = params["min_asset_weight"]
    max_w = params["max_asset_weight"]

    model.w = pyo.Var(model.Assets, within=pyo.Reals, bounds=(min_w, max_w))

    er = {
        0: params["expected_return_asset0"],
        1: params["expected_return_asset1"],
        2: params["expected_return_asset2"],
        3: params["expected_return_asset3"],
    }

    model.budget = pyo.Constraint(
        expr=sum(model.w[i] for i in model.Assets) == params["budget_sum"]
    )

    model.return_req = pyo.Constraint(
        expr=sum(er[i] * model.w[i] for i in model.Assets)
        >= params["min_portfolio_return"]
    )

    # Minimize the quadratic portfolio variance directly as the objective.
    model.obj = pyo.Objective(
        expr=sum(model.w[i] * model.w[i] for i in model.Assets),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}