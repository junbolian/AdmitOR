import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    n = len(dist)

    model = pyo.ConcreteModel()
    model.N = pyo.RangeSet(0, n - 1)
    model.Nc = pyo.RangeSet(1, n - 1)  # customer nodes
    model.A = pyo.Set(initialize=[
        (i, j) for i in model.N for j in model.N if i != j
    ])

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(model.Nc, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(dist[i][j] * mdl.x[i, j] for (i, j) in mdl.A)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Degree constraints
    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.N if j != i) == 1

    model.out_con = pyo.Constraint(model.N, rule=out_rule)

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.N if i != j) == 1

    model.in_con = pyo.Constraint(model.N, rule=in_rule)

    # MTZ subtour elimination
    def mtz_rule(mdl, i, j):
        return mdl.u[i] - mdl.u[j] + (n - 1) * mdl.x[i, j] <= n - 2

    model.mtz_con = pyo.Constraint(
        [(i, j) for i in model.Nc for j in model.Nc if i != j], rule=mtz_rule
    )

    def u_bound_rule(mdl, i):
        return mdl.u[i] <= n - 1

    model.u_bound = pyo.Constraint(model.Nc, rule=u_bound_rule)

    def u_lb_rule(mdl, i):
        return mdl.u[i] >= 1

    model.u_lb = pyo.Constraint(model.Nc, rule=u_lb_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}