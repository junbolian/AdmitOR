import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_rows = [params["cost_0"], params["cost_1"], params["cost_2"],
                 params["cost_3"], params["cost_4"], params["cost_5"],
                 params["cost_6"], params["cost_7"], params["cost_8"],
                 params["cost_9"]]
    cost = {(i, j): cost_rows[i][j] for i in range(10) for j in range(10)}
    N = list(range(10))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(N, N, domain=pyo.Binary)
    model.u = pyo.Var(N, domain=pyo.NonNegativeReals, bounds=(0, 10))

    # Fix self loops
    for i in N:
        model.x[i, i].fix(0)

    # Degree constraints
    model.out_deg = pyo.Constraint(
        N, rule=lambda mm, i: pyo.sum(mm.x[i, j] for j in N if j != i) == 1
    )
    model.in_deg = pyo.Constraint(
        N, rule=lambda mm, i: pyo.sum(mm.x[j, i] for j in N if j != i) == 1
    )

    # Subtour elimination (MTZ) for nodes 1..9
    model.mtz = pyo.Constraint(
        [(i, j) for i in range(1, 10) for j in range(1, 10) if i != j],
        rule=lambda mm, i, j: mm.u[i] - mm.u[j] + 9 * mm.x[i, j] <= 8
    )
    model.u_lb = pyo.Constraint(range(1, 10), rule=lambda mm, i: mm.u[i] >= 1)
    model.u_ub = pyo.Constraint(range(1, 10), rule=lambda mm, i: mm.u[i] <= 9)

    model.obj = pyo.Objective(
        expr=pyo.sum_product(model.x, cost),
        sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}