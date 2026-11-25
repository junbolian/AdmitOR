import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    flow = params["flow_matrix"]
    dist = params["distance_matrix"]
    n = params["num_facilities"]
    m = params["num_locations"]

    def F(i, k):
        return flow[i * m + k]

    def D(j, l):
        return dist[j * m + l]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, n - 1)
    model.J = pyo.RangeSet(0, m - 1)
    model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)

    def obj_rule(md):
        return sum(
            F(i, k) * D(j, l) * md.x[i, j] * md.x[k, l]
            for i in md.I for k in md.I
            for j in md.J for l in md.J
            if i < k
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    model.assign_facility = pyo.Constraint(
        model.I, rule=lambda md, i: sum(md.x[i, j] for j in md.J) == 1
    )
    model.assign_location = pyo.Constraint(
        model.J, rule=lambda md, j: sum(md.x[i, j] for i in md.I) == 1
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}