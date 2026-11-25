import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["coordinates"]
    dist = params["distance_matrix"]
    K = params["num_vehicles"]
    n_clinics = params["num_clinics"]

    nodes = list(range(n_clinics + 1))
    clinics = list(range(1, n_clinics + 1))
    vehicles = list(range(K))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=nodes)
    model.C = pyo.Set(initialize=clinics)
    model.K = pyo.Set(initialize=vehicles)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    # MTZ ordering variables to eliminate subtours
    model.u = pyo.Var(model.C, bounds=(1, n_clinics))

    model.x = pyo.Var(model.A, model.K, domain=pyo.Binary)
    model.y = pyo.Var(model.V, model.K, domain=pyo.Binary)

    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j, k] for (i, j) in arcs for k in vehicles)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each clinic visited exactly once
    def visit_rule(m, j):
        return sum(m.x[i, j, k] for i in nodes if i != j for k in vehicles) == 1

    model.visit = pyo.Constraint(model.C, rule=visit_rule)

    # Flow conservation per vehicle
    def flow_rule(m, j, k):
        out_ = sum(m.x[j, i2, k] for i2 in nodes if i2 != j)
        in_ = sum(m.x[i2, j, k] for i2 in nodes if i2 != j)
        return out_ == in_

    model.flow = pyo.Constraint(model.V, model.K, rule=flow_rule)

    # Each vehicle leaves node 0 at most once (used or not)
    def depart_rule(m, k):
        return sum(m.x[0, j, k] for j in clinics) <= 1

    model.depart = pyo.Constraint(model.K, rule=depart_rule)

    # Linking y and x
    def ylink_rule(m, i, k):
        if i == 0:
            return m.y[0, k] == sum(m.x[0, j, k] for j in clinics)
        return m.y[i, k] == sum(m.x[j, i, k] for j in nodes if j != i)

    model.ylink = pyo.Constraint(model.V, model.K, rule=ylink_rule)

    # MTZ subtour elimination
    def mtz_rule(m, i, j, k):
        return m.u[i] - m.u[j] + n_clinics * m.x[i, j, k] <= n_clinics - 1

    model.mtz = pyo.Constraint(
        [(i, j, k) for (i, j) in arcs if i != 0 and j != 0 for k in vehicles],
        rule=mtz_rule,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}