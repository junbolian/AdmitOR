import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]
    num_vehicles = params["num_vehicles"]
    num_workstations = params["num_workstations"]

    V = range(num_vehicles)
    W = range(num_workstations)
    pos = range(num_vehicles)

    p = {(i, j): processing_times[i][j] for i in V for j in W}

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=list(V))
    model.W = pyo.Set(initialize=list(W))
    model.P = pyo.Set(initialize=list(pos))

    model.x = pyo.Var(model.V, model.P, domain=pyo.Binary)
    model.C = pyo.Var(model.V, model.W, domain=pyo.NonNegativeReals)
    model.Cmax = pyo.Var(domain=pyo.NonNegativeReals)

    # Each vehicle assigned exactly one position
    model.assign = pyo.Constraint(model.V, rule=lambda m, i: sum(m.x[i, k] for k in m.P) == 1)
    # Each position gets exactly one vehicle
    model.slot = pyo.Constraint(model.P, rule=lambda m, k: sum(m.x[i, k] for i in m.V) == 1)

    # Makespan
    model.makespan = pyo.Constraint(model.V, rule=lambda m, i: m.Cmax >= m.C[i, num_workstations - 1])

    # Workstation 0 completion times
    def c0_rule(m, i, k):
        if k == 0:
            return m.C[i, 0] >= p[i, 0]
        return m.C[i, 0] >= p[i, 0] + sum(
            p[j, 0] * m.x[j, kk] for j in V for kk in pos if kk < k
        )
    model.c0 = pyo.Constraint(model.V, model.P, rule=c0_rule)

    # Subsequent workstations
    def cj_rule(m, i, j, k):
        if j == 0:
            return pyo.Constraint.Skip
        if k == 0:
            return m.C[i, j] >= m.C[i, j - 1] + p[i, j]
        return m.C[i, j] >= m.C[i, j - 1] + p[i, j] + sum(
            p[o, j] * m.x[o, kk] for o in V for kk in pos if kk < k
        )
    model.cj = pyo.Constraint(model.V, model.W, model.P, rule=cj_rule)

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}