import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    n = len(cost)

    model = pyo.ConcreteModel()

    # x[i,j] = 1 if the tour goes from city i to city j
    model.x = pyo.Var(range(n), range(n), domain=pyo.Binary)

    # Objective: minimize total travel cost
    model.objective_expr = pyo.Expression(
        expr=sum(cost[i][j] * model.x[i, j]
                 for i in range(n)
                 for j in range(n)
                 if i != j)
    )
    model.obj = pyo.Objective(expr=model.objective_expr, sense=pyo.minimize)

    # Each city is departed from exactly once
    model.out_deg = pyo.ConstraintList()
    for i in range(n):
        model.out_deg.add(
            sum(model.x[i, j] for j in range(n) if j != i) == 1
        )

    # Each city is arrived at exactly once
    model.in_deg = pyo.ConstraintList()
    for j in range(n):
        model.in_deg.add(
            sum(model.x[i, j] for i in range(n) if i != j) == 1
        )

    # Subtour elimination (Miller-Tucker-Zemlin)
    model.u = pyo.Var(range(n), bounds=(1, n - 1))
    model.subtour = pyo.ConstraintList()
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.subtour.add(
                    model.u[i] - model.u[j] + n * model.x[i, j] <= n - 1
                )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible"}