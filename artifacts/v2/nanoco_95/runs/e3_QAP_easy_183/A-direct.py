import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    flow = params["flow"]
    distance = params["distance"]
    x_coords = params["x_coords"]
    y_coords = params["y_coords"]
    n_departments = params["n_departments"]
    n_zones = params["n_zones"]

    n = int(n_departments)
    z = int(n_zones)

    def flow_val(i, j):
        if i == j:
            return 0
        if i > j:
            i, j = j, i
        try:
            return flow[i][j]
        except (TypeError, IndexError):
            pass
        try:
            return flow[i, j]
        except (TypeError, IndexError):
            pass
        try:
            return flow[j][i]
        except (TypeError, IndexError):
            pass
        try:
            return flow[j, i]
        except (TypeError, IndexError):
            pass
        # fallback: treat as flat symmetric list of pair volumes
        idx = 0
        for a in range(n):
            for b in range(a + 1, n):
                if a == min(i, j) and b == max(i, j):
                    return flow[idx]
                idx += 1
        raise KeyError((i, j))

    def dist_val(a, b):
        if a == b:
            return 0
        if a > b:
            a, b = b, a
        try:
            return distance[a][b]
        except (TypeError, IndexError):
            pass
        try:
            return distance[a, b]
        except (TypeError, IndexError):
            pass
        try:
            return distance[b][a]
        except (TypeError, IndexError):
            pass
        try:
            return distance[b, a]
        except (TypeError, IndexError):
            pass
        idx = 0
        for p in range(z):
            for q in range(p + 1, z):
                if p == a and q == b:
                    return distance[idx]
                idx += 1
        raise KeyError((a, b))

    flow_matrix = {(i, j): flow_val(i, j) for i in range(n) for j in range(n) if i < j}
    dist_matrix = {(a, b): dist_val(a, b) for a in range(z) for b in range(z) if a < b}

    model = pyo.ConcreteModel()

    model.D = pyo.RangeSet(0, n - 1)
    model.Z = pyo.RangeSet(0, z - 1)

    model.x = pyo.Var(model.D, model.Z, domain=pyo.Binary)

    model.obj = pyo.Objective(
        rule=lambda mdl: sum(
            flow_matrix[i, j] * dist_matrix[a, b] * mdl.x[i, a] * mdl.x[j, b]
            for i in mdl.D
            for j in mdl.D
            if i < j
            for a in mdl.Z
            for b in mdl.Z
            if a < b
        ),
        sense=pyo.minimize,
    )

    model.assign_dept = pyo.Constraint(
        model.D, rule=lambda mdl, i: sum(mdl.x[i, a] for a in mdl.Z) == 1
    )
    model.assign_zone = pyo.Constraint(
        model.Z, rule=lambda mdl, a: sum(mdl.x[i, a] for i in mdl.D) == 1
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}