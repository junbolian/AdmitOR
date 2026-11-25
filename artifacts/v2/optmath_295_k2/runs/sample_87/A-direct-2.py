import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    expected_returns = list(params["expected_returns"])
    min_return = float(params["min_return"])
    max_weight = float(params["max_weight"])
    budget_sum_weights = float(params["budget_sum_weights"])

    cov = [
        [0.0325, 0.0234, 0.0198, 0.0112, 0.0176],
        [0.0234, 0.0412, 0.0247, 0.0158, 0.0208],
        [0.0198, 0.0247, 0.0536, 0.0131, 0.0265],
        [0.0112, 0.0158, 0.0131, 0.0216, 0.0098],
        [0.0176, 0.0208, 0.0265, 0.0098, 0.0307],
    ]

    n = 5

    model = pyo.ConcreteModel()
    model.x = pyo.Var(range(n), bounds=(0, max_weight))

    # Quadratic objective: HiGHS requires objective to be added directly (not via Expression)
    model.obj = pyo.Objective(
        expr=sum(
            cov[i][j] * model.x[i] * model.x[j]
            for i in range(n)
            for j in range(n)
        ),
        sense=pyo.minimize,
    )

    model.budget = pyo.Constraint(
        expr=sum(model.x[i] for i in range(n)) == budget_sum_weights
    )

    model.ret = pyo.Constraint(
        expr=sum(expected_returns[i] * model.x[i] for i in range(n)) >= min_return
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or unsolved"}

    return {"objective": obj_val, "status": "optimal"}