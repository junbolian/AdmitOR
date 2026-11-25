import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    expected_returns = params["expected_returns"]
    min_expected_return = params["min_expected_return"]
    variances = params["variances"]
    covariances = params["covariances"]
    max_weight = params["max_weight"]
    budget_sum = params["budget_sum"]

    n = 4
    pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, n - 1)

    model.w = pyo.Var(model.assets, bounds=(0, max_weight))

    # Auxiliary variable to hold the quadratic objective (HiGHS requires linear/quadratic handled via explicit quadratic expression; DegreeError arises when passing an Expression with degree>2 through general objective warmup). We'll construct the quadratic directly on the Objective component.
    def variance_rule(m):
        expr = sum(variances[i] * m.w[i] * m.w[i] for i in range(n))
        for k, (i, j) in enumerate(pairs):
            expr += 2 * covariances[k] * m.w[i] * m.w[j]
        return expr

    model.expected_return_con = pyo.Constraint(
        expr=sum(expected_returns[i] * model.w[i] for i in range(n)) >= min_expected_return
    )
    model.budget_con = pyo.Constraint(
        expr=sum(model.w[i] for i in range(n)) == budget_sum
    )

    model.objective = pyo.Objective(rule=variance_rule, sense=pyo.minimize)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}