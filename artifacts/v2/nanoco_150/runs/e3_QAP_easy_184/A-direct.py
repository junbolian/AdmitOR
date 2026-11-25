import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    flow_matrix = params["flow_matrix"]
    distance_matrix = params["distance_matrix"]
    num_units = int(params["num_units"])
    num_rooms = int(params["num_rooms"])

    units = list(range(num_units))
    rooms = list(range(num_rooms))

    model = pyo.ConcreteModel()
    model.U = pyo.Set(initialize=units)
    model.R = pyo.Set(initialize=rooms)
    model.x = pyo.Var(model.U, model.R, domain=pyo.Binary)

    # Linearized QAP: y[u,v,i,j] = x[u,i] * x[v,j] for u<v, i!=j
    pairs_uv = [(u, v) for u in units for v in units if u < v]
    pairs_ij = [(i, j) for i in rooms for j in rooms if i != j]
    model.PUV = pyo.Set(initialize=pairs_uv, dimen=2)
    model.PIJ = pyo.Set(initialize=pairs_ij, dimen=2)
    model.y = pyo.Var(model.PUV, model.PIJ, domain=pyo.Binary)

    # Link constraints: y[u,v,i,j] == x[u,i] AND x[v,j]
    model.link_a = pyo.Constraint(
        model.PUV, model.PIJ,
        rule=lambda m, u, v, i, j: m.y[u, v, i, j] <= m.x[u, i],
    )
    model.link_b = pyo.Constraint(
        model.PUV, model.PIJ,
        rule=lambda m, u, v, i, j: m.y[u, v, i, j] <= m.x[v, j],
    )
    model.link_c = pyo.Constraint(
        model.PUV, model.PIJ,
        rule=lambda m, u, v, i, j: m.y[u, v, i, j] >= m.x[u, i] + m.x[v, j] - 1,
    )

    def obj_rule(m):
        total = 0
        for (u, v) in pairs_uv:
            w = float(flow_matrix[u][v]) + float(flow_matrix[v][u])
            for (i, j) in pairs_ij:
                d = float(distance_matrix[i][j])
                total += w * d * m.y[u, v, i, j]
        return total

    model.cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.unit_assign = pyo.ConstraintList()
    for u in units:
        model.unit_assign.add(sum(model.x[u, i] for i in rooms) == 1)

    model.room_assign = pyo.ConstraintList()
    for i in rooms:
        model.room_assign.add(sum(model.x[u, i] for u in units) == 1)

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))

    return {"objective": obj_val, "status": "optimal"}