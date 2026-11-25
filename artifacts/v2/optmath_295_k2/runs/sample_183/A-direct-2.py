import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    n = params["num_cities"]
    pos_lb = params["position_lower_bound"]
    pos_ub = params["position_upper_bound"]
    start = params["start_city"]

    cities = list(range(n))

    # Normalize bounds into per-city lookups
    def lb_of(i):
        try:
            return pos_lb[i]
        except (TypeError, IndexError, KeyError):
            return pos_lb

    def ub_of(i):
        try:
            return pos_ub[i]
        except (TypeError, IndexError, KeyError):
            return pos_ub

    model = pyo.ConcreteModel()
    model.C = pyo.Set(initialize=cities)
    model.A = pyo.Set(initialize=[(i, j) for i in cities for j in cities if i != j])

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.C,
        domain=pyo.NonNegativeReals,
        bounds=lambda m, i: (lb_of(i), ub_of(i)),
    )

    model.obj = pyo.Objective(
        expr=sum(dist[i][j] * model.x[i, j] for (i, j) in model.A),
        sense=pyo.minimize,
    )

    model.out_deg = pyo.Constraint(
        model.C, rule=lambda m, i: sum(m.x[i, j] for j in cities if j != i) == 1
    )
    model.in_deg = pyo.Constraint(
        model.C, rule=lambda m, j: sum(m.x[i, j] for i in cities if i != j) == 1
    )

    def mt(bm, i, j):
        return bm.u[i] - bm.u[j] + n * bm.x[i, j] <= n - 1

    model.subtour = pyo.Constraint(model.A, rule=mt)
    model.start_pos = pyo.Constraint(expr=model.u[start] == 0)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}