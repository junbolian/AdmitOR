import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    n = len(cost)

    model = pyo.ConcreteModel()
    model.x = pyo.Var(range(n), range(n), within=pyo.Binary)
    model.u = pyo.Var(range(n), within=pyo.NonNegativeReals, bounds=(0, n - 1))

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in range(n) for j in range(n) if i != j)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.out_deg = pyo.ConstraintList()
    model.in_deg = pyo.ConstraintList()
    for i in range(n):
        model.out_deg.add(sum(model.x[i, j] for j in range(n) if j != i) == 1)
        model.in_deg.add(sum(model.x[j, i] for j in range(n) if j != i) == 1)

    # MTZ subtour elimination
    model.mtz = pyo.ConstraintList()
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.mtz.add(
                    model.u[i] - model.u[j] + (n - 1) * model.x[i, j] <= n - 2
                )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}