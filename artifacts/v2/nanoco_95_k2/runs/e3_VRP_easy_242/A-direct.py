import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 8
    nodes = list(range(n + 1))
    clinics = list(range(1, n + 1))
    K = 2
    vehicles = list(range(K))

    dist = {}
    for i in nodes:
        for j in nodes:
            if i == j:
                dist[i, j] = 0.0
            elif i == 0 and j in clinics:
                dist[i, j] = params["dist_0_%d" % j]
            elif j == 0 and i in clinics:
                dist[i, j] = params["dist_0_%d" % i]
            elif i in clinics and j in clinics:
                a, b = (i, j) if i < j else (j, i)
                dist[i, j] = params["dist_%d_%d" % (a, b)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, nodes, vehicles, within=pyo.Binary)
    model.u = pyo.Var(clinics, vehicles, within=pyo.NonNegativeReals, bounds=(1, n))

    def obj_rule(mdl):
        return sum(dist[i, j] * mdl.x[i, j, k]
                   for i in nodes for j in nodes for k in vehicles)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.visit = pyo.Constraint(
        clinics,
        rule=lambda mdl, j: sum(mdl.x[i, j, k] for i in nodes for k in vehicles
                                if i != j) == 1
    )

    model.leave = pyo.Constraint(
        clinics,
        rule=lambda mdl, i: sum(mdl.x[i, j, k] for j in nodes for k in vehicles
                                if j != i) == 1
    )

    model.depot_out = pyo.Constraint(
        vehicles,
        rule=lambda mdl, k: sum(mdl.x[0, j, k] for j in clinics) <= 1
    )

    model.depot_in = pyo.Constraint(
        vehicles,
        rule=lambda mdl, k: sum(mdl.x[i, 0, k] for i in clinics) <= 1
    )

    model.route_balance = pyo.Constraint(
        nodes, vehicles,
        rule=lambda mdl, p, k: sum(mdl.x[i, p, k] for i in nodes if i != p)
        - sum(mdl.x[p, j, k] for j in nodes if j != p) == 0
    )

    model.subtour = pyo.Constraint(
        clinics, clinics, vehicles,
        rule=lambda mdl, i, j, k: mdl.u[i, k] - mdl.u[j, k] + n * mdl.x[i, j, k] <= n - 1
        if i != j else pyo.Constraint.Skip
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}